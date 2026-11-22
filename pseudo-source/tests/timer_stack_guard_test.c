#include "interrupts.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CHECK(x) do { if (!(x)) { fprintf(stderr,"Stack guard check %d: %s\n",__LINE__,#x);exit(1); } } while (0)
typedef struct {char op;uint16_t address;uint8_t value;} Event;
typedef struct {
    uint8_t memory[65536];Event events[8];unsigned attempts,used,fail,reads_4f;
    bool mutate_first_4f;unsigned action;PcmPlatform platform;
} Fixture;
static Fixture fixture;
static Pcm pcm;

static PcmStatus read8(void *ctx,uint16_t a,uint8_t *value)
{
    Fixture *f=ctx;uint8_t sampled=f->memory[a];
    if (f->used<8) f->events[f->used++]=(Event){'R',a,sampled};
    if (++f->attempts==f->fail) return PCM_NO_HARDWARE;
    *value=sampled;
    if (a==0x004f && ++f->reads_4f==1 && f->mutate_first_4f)
        f->memory[a]^=0x80u;
    if (a==0x004f && f->reads_4f==1 && f->action==2) f->memory[a]^=0x04u;
    if (a==0x003a && f->action==3) f->memory[a]^=0x80u;
    return PCM_OK;
}
static PcmStatus write8(void *ctx,uint16_t a,uint8_t value)
{
    Fixture *f=ctx;
    if (f->used<8) f->events[f->used++]=(Event){'W',a,value};
    if (++f->attempts==f->fail) return PCM_NO_HARDWARE;
    f->memory[a]=value;
    if (a==0x003a && f->action==4) f->memory[0x004f]^=0xc0u;
    return PCM_OK;
}
static void init(void)
{
    memset(&fixture,0,sizeof(fixture));memset(&pcm,0,sizeof(pcm));
    fixture.platform.context=&fixture;fixture.platform.read8=read8;
    fixture.platform.write8=write8;pcm.platform=&fixture.platform;
}
static void exhaustive_thresholds(void)
{
    init();
    for (unsigned busy=0;busy<2;++busy) {
        for (unsigned x=0;x<65536;++x) {
            fixture.memory[0x004f]=(uint8_t)(busy?0x97u:0x93u);
            fixture.memory[0x003a]=0x51u;
            fixture.used=fixture.attempts=fixture.reads_4f=0;
            bool recovery=true;
            CHECK(pcm_timer_stack_guard(&pcm,(uint16_t)x,&recovery)==PCM_OK);
            bool expect=x<0x03b0u || x>(busy?0x03eeu:0x03f7u);
            CHECK(recovery==expect);
            CHECK(fixture.used==(expect?5u:1u));
            CHECK(fixture.events[0].op=='R' && fixture.events[0].address==0x004f);
            if (expect) {
                CHECK(fixture.events[1].op=='R' && fixture.events[1].address==0x003a);
                CHECK(fixture.events[2].op=='W' && fixture.events[2].address==0x003a);
                CHECK(fixture.events[3].op=='R' && fixture.events[3].address==0x004f);
                CHECK(fixture.events[4].op=='W' && fixture.events[4].address==0x004f);
                CHECK(fixture.memory[0x003a]==0x59u);
                CHECK(fixture.memory[0x004f]==(uint8_t)((busy?0x97u:0x93u)&~0x04u));
            } else {
                CHECK(fixture.memory[0x003a]==0x51u);
                CHECK(fixture.memory[0x004f]==(busy?0x97u:0x93u));
            }
        }
    }
}
static void prefixes_and_fresh_reads(void)
{
    for (unsigned fail=1;fail<=5;++fail) {
        init();fixture.fail=fail;fixture.memory[0x003a]=0x20u;fixture.memory[0x004f]=0x84u;
        bool recovery=true;
        CHECK(pcm_timer_stack_guard(&pcm,0x03efu,&recovery)==PCM_NO_HARDWARE);
        CHECK(!recovery && fixture.used==fail);
        CHECK(fixture.memory[0x003a]==(fail>=4?0x28u:0x20u));
        CHECK(fixture.memory[0x004f]==0x84u);
    }
    init();fixture.memory[0x003a]=0x40u;fixture.memory[0x004f]=0x04u;
    fixture.mutate_first_4f=true;bool recovery=false;
    CHECK(pcm_timer_stack_guard(&pcm,0x03efu,&recovery)==PCM_OK && recovery);
    CHECK(fixture.memory[0x004f]==0x80u); /* Preserve freshly changed bit7. */
    CHECK(fixture.memory[0x003a]==0x48u);
    init();CHECK(pcm_timer_stack_guard(&pcm,0,NULL)==PCM_BAD_CONFIGURATION && fixture.used==0);
    pcm.platform=NULL;recovery=true;
    CHECK(pcm_timer_stack_guard(&pcm,0,&recovery)==PCM_NO_HARDWARE && !recovery);
}
int main(int argc,char **argv)
{
    if (argc==2 && strcmp(argv[1],"--cases")==0) {
        unsigned x,flags,faults,action,fail;
        while (scanf("%u %u %u %u %u",&x,&flags,&faults,&action,&fail)==5) {
            CHECK(x<65536 && flags<256 && faults<256 && action<5 && fail<8);
            init();fixture.memory[0x004f]=(uint8_t)flags;fixture.memory[0x003a]=(uint8_t)faults;
            fixture.action=action;fixture.mutate_first_4f=action==1;fixture.fail=fail;
            bool recovery=true;PcmStatus status=pcm_timer_stack_guard(&pcm,(uint16_t)x,&recovery);
            printf("{\"status\":%u,\"recovery\":%u,\"flags\":%u,\"faults\":%u,\"events\":[",
                (unsigned)status,(unsigned)recovery,(unsigned)fixture.memory[0x004f],(unsigned)fixture.memory[0x003a]);
            for (unsigned i=0;i<fixture.used;++i) { const Event *e=&fixture.events[i];
                printf("%s[\"%c\",%u,%u]",i?",":"",e->op,(unsigned)e->address,(unsigned)e->value); }
            puts("]}");
        }
        return 0;
    }
    CHECK(argc==1 || (argc==2 && strcmp(argv[1],"--contracts")==0));
    exhaustive_thresholds();prefixes_and_fresh_reads();
    puts("131072 timer stack-guard threshold cases and ordered failure-prefix contracts pass.");
    return 0;
}
