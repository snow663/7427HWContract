/* Source/HC11 E684/E6AC/E69C/D4EB..D4F7 diagnostic prefix fixture.
 * ROM input is supplied by the independently hash-checked Python caller.
 * All RAM is synthetic; there is no target electrical operation. */
#include "control.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define CHECK(x) do {if(!(x)){fprintf(stderr,"D4EB fixture:%d %s\n",__LINE__,#x);exit(3);}}while(0)
typedef struct {
    PcmPlatform platform;
    uint8_t mem[65536];
    uint16_t addresses[1024];
    unsigned count,fail_at;
} Fixture;
static PcmStatus read8(void *opaque,uint16_t address,uint8_t *value)
{
    Fixture *f=opaque;
    CHECK(f->count<1024);
    f->addresses[f->count++]=address;
    if(f->fail_at!=0 && f->count==f->fail_at)return PCM_NO_HARDWARE;
    *value=f->mem[address];
    return PCM_OK;
}
static PcmStatus write8(void *opaque,uint16_t address,uint8_t value)
{
    Fixture *f=opaque;
    CHECK(f->count<1024);
    f->addresses[f->count++]=address;
    if(f->fail_at!=0 && f->count==f->fail_at)return PCM_NO_HARDWARE;
    f->mem[address]=value;
    return PCM_OK;
}
static PcmStatus run(Pcm *pcm,unsigned mode)
{
    switch(mode) {
    case 0:return pcm_transmission_fault_gate_684(pcm);
    case 1:return pcm_transmission_fault_gate_6ac(pcm);
    case 2:return pcm_transmission_fault_gate_69c(pcm);
    case 3:return pcm_transmission_d4eb_prefix(pcm);
    default:return PCM_BAD_CONFIGURATION;
    }
}
static void setup(Fixture *f,Pcm *pcm)
{
    memset(f,0,sizeof(*f));
    memset(pcm,0,sizeof(*pcm));
    f->platform.context=f;
    f->platform.read8=read8;
    f->platform.write8=write8;
    pcm->platform=&f->platform;
}
static void contracts(void)
{
    static Fixture f;Pcm pcm;bool active;
    setup(&f,&pcm);
    f.mem[0x001d]=0x80;f.mem[0x0098]=0x11;
    CHECK(run(&pcm,0)==PCM_OK);
    CHECK(f.mem[0x0098]==0x91);
    CHECK(f.count==3 && f.addresses[0]==0x001d &&
          f.addresses[1]==0x0098 && f.addresses[2]==0x0098);
    for(unsigned fail=1;fail<=3;fail++) {
        setup(&f,&pcm);
        f.mem[0x001d]=0x80;f.mem[0x0098]=0x11;f.fail_at=fail;
        CHECK(run(&pcm,0)==PCM_NO_HARDWARE);
        CHECK(f.count==fail && f.mem[0x0098]==0x11);
    }
    setup(&f,&pcm);active=true;
    CHECK(pcm_transmission_mask_scan(&pcm,0xe743,&active)==PCM_OK && !active);
    CHECK(f.count==36 && f.addresses[0]==0x5b3c &&
          f.addresses[1]==0x5b33 && f.addresses[2]==0x001e &&
          f.addresses[3]==0xe74c && f.addresses[35]==0xe744);
    setup(&f,&pcm);active=false;
    f.mem[0x5b3c]=0;f.mem[0x5b33]=1;
    f.mem[0x001e]=1;f.mem[0xe74c]=1;
    CHECK(pcm_transmission_mask_scan(&pcm,0xe743,&active)==PCM_OK && active);
    CHECK(f.count==4);
    for(unsigned fail=1;fail<=4;fail++) {
        setup(&f,&pcm);f.fail_at=fail;active=true;
        CHECK(pcm_transmission_mask_scan(&pcm,0xe743,&active)==PCM_NO_HARDWARE);
        CHECK(active && f.count==fail);
    }
    setup(&f,&pcm);
    f.mem[0x0098]=0x53;f.mem[0x0099]=0xa7;f.mem[0x0084]=0xf8;
    CHECK(run(&pcm,3)==PCM_OK);
    CHECK(f.mem[0x0098]==0x53 && f.mem[0x0099]==0xa4 && f.mem[0x0084]==0);
    /* Fail just after first completed flag write; earlier changes survive,
       later gate and the $0084 clear must not execute. */
    setup(&f,&pcm);
    f.mem[0x0098]=0xff;f.mem[0x0099]=0xff;f.mem[0x0084]=0xab;
    f.fail_at=5;
    CHECK(run(&pcm,3)==PCM_NO_HARDWARE);
    CHECK(f.mem[0x0098]==0x7f && f.mem[0x0099]==0xff && f.mem[0x0084]==0xab);
    CHECK(run(NULL,3)==PCM_BAD_CONFIGURATION);
    CHECK(pcm_transmission_mask_scan(NULL,0xe743,&active)==PCM_BAD_CONFIGURATION);
    CHECK(pcm_transmission_mask_scan(&pcm,0xe743,NULL)==PCM_BAD_CONFIGURATION);
    puts("D4EB prefix diagnostics: table order, mask, retention and fail-prefix contracts pass.");
}
int main(int argc,char **argv)
{
    if(argc==2 && strcmp(argv[1],"--contracts")==0) {
        contracts();
        return 0;
    }
    if(argc!=2)return 2;
    FILE *file=fopen(argv[1],"rb");if(file==NULL)return 2;
    static uint8_t rom[65536];
    int complete=fread(rom,1,sizeof(rom),file)==sizeof(rom);
    fclose(file);if(!complete)return 2;
    static Fixture f;Pcm pcm;
    unsigned mode,edits;
    while(scanf("%u %u",&mode,&edits)==2) {
        CHECK(edits<1024);
        setup(&f,&pcm);
        memcpy(f.mem,rom,sizeof(rom));
        for(unsigned k=0;k<edits;++k) {
            unsigned addr,value;
            CHECK(scanf("%u %u",&addr,&value)==2 && addr<65536 && value<256);
            f.mem[addr]=(uint8_t)value;
        }
        PcmStatus status=run(&pcm,mode);
        printf("{\"status\":%u,\"state\":[%u,%u,%u]}\n",
               (unsigned)status,f.mem[0x0084],f.mem[0x0098],f.mem[0x0099]);
    }
    return ferror(stdin)?2:0;
}
