#include "scheduler.h"
#include "control.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define CHECK(x) do{if(!(x)){fprintf(stderr,"Slot03 %s:%d %s\n",__FILE__,__LINE__,#x);exit(1);}}while(0)
typedef struct {
    PcmPlatform platform;
    uint8_t bytes[65536];
    uint16_t called[4];
    unsigned call_count,read_count,write_count;
    bool fail_write,fail_read,fail_extension;
} Fixture;
static PcmStatus r8(void*ctx,uint16_t address,uint8_t*out)
{
    Fixture*f=ctx;++f->read_count;
    if(f->fail_read)return PCM_NO_HARDWARE;
    *out=f->bytes[address];return PCM_OK;
}
static PcmStatus w8(void*ctx,uint16_t address,uint8_t value)
{
    Fixture*f=ctx;++f->write_count;
    if(f->fail_write)return PCM_NO_HARDWARE;
    f->bytes[address]=value;return PCM_OK;
}
static PcmStatus at(void*ctx,uint16_t address)
{
    Fixture*f=ctx;CHECK(f->call_count<4);
    f->called[f->call_count++]=address;
    if(address==0x1806u && f->fail_extension)return PCM_NO_HARDWARE;
    /* Deliberate actual D4EB source boundary, no invented TCC success. */
    return address==0xd4ebu?PCM_NO_HARDWARE:PCM_OK;
}
static void init(Fixture*f,Pcm*p)
{
    memset(f,0,sizeof(*f));memset(p,0,sizeof(*p));
    f->platform.context=f;f->platform.read8=r8;f->platform.write8=w8;
    f->platform.enable_resident_slow_slots=true;
    p->platform=&f->platform;p->unresolved_task=PCM_TASK_COUNT;
}
int main(int argc,char**argv)
{
    if(argc==2 && strcmp(argv[1],"--contracts")!=0)return 2;
    static Fixture f;Pcm p;
    init(&f,&p);f.platform.enable_resident_slow_slots=false;
    CHECK(pcm_slot_03(&p)==PCM_UNIMPLEMENTED && p.unresolved_task==PCM_SLOT_03);
    CHECK(f.read_count==0 && f.write_count==0 && f.call_count==0);
    init(&f,&p);
    CHECK(pcm_slot_03(&p)==PCM_UNIMPLEMENTED && p.unresolved_task==PCM_SLOT_03);
    CHECK(f.read_count==1 && f.write_count==1 && f.bytes[0x0f00]==247);
    init(&f,&p);f.bytes[0x86]=0x40;
    CHECK(pcm_slot_03(&p)==PCM_UNIMPLEMENTED && f.bytes[0x0f00]==0);
    CHECK(f.read_count==1 && f.call_count==0);
    init(&f,&p);f.bytes[0x86]=0x40;f.platform.call_address=at;
    CHECK(pcm_slot_03(&p)==PCM_NO_HARDWARE);
    CHECK(f.call_count==2 && f.called[0]==0x1806 && f.called[1]==0xd4eb);
    CHECK(f.bytes[0x0f00]==247 && f.write_count==1);
    init(&f,&p);f.bytes[0x86]=0x40;f.platform.call_address=at;f.fail_extension=true;
    CHECK(pcm_slot_03(&p)==PCM_NO_HARDWARE);
    CHECK(f.call_count==1 && f.called[0]==0x1806 && f.write_count==0);
    init(&f,&p);f.platform.call_address=at;f.fail_write=true;
    CHECK(pcm_slot_03(&p)==PCM_NO_HARDWARE && f.call_count==0 && f.write_count==1);
    init(&f,&p);f.fail_read=true;
    CHECK(pcm_slot_03(&p)==PCM_NO_HARDWARE && f.write_count==0);
    CHECK(pcm_slot_03(NULL)==PCM_BAD_CONFIGURATION);
    puts("Slot03 $1806 optional gate, F7 marker and D4EB source boundary verified.");
    return 0;
}
