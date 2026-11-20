#include "fuel.h"
#include "hardware.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define CHECK(x) do { if (!(x)) { fprintf(stderr,"Ignition precheck %s:%d: %s\n",__FILE__,__LINE__,#x);exit(1); } } while (0)

typedef struct { char kind; unsigned width; uint16_t address,value; } Event;
typedef struct {
    uint8_t memory[65536];
    Event events[96];
    unsigned used,attempts,fail_at;
    bool irq_masked;
    PcmPlatform platform;
} Fixture;
static PcmStatus record(Fixture *f,char kind,unsigned width,uint16_t address,uint16_t value)
{
    if (++f->attempts==f->fail_at) return PCM_NO_HARDWARE;
    CHECK(f->used<sizeof(f->events)/sizeof(f->events[0]));
    f->events[f->used++]=(Event){kind,width,address,value};
    return PCM_OK;
}
static PcmStatus read8(void *context,uint16_t address,uint8_t *out)
{
    Fixture *f=context;uint8_t value=f->memory[address];
    PcmStatus status=record(f,'R',8,address,value);
    if (status==PCM_OK) *out=value;
    return status;
}
static PcmStatus read16(void *context,uint16_t address,uint16_t *out)
{
    Fixture *f=context;
    uint16_t value=(uint16_t)((uint16_t)f->memory[address]*256u+
                                f->memory[(uint16_t)(address+1u)]);
    PcmStatus status=record(f,'R',16,address,value);
    if (status==PCM_OK) *out=value;
    return status;
}
static PcmStatus write8(void *context,uint16_t address,uint8_t value)
{
    Fixture *f=context;
    PcmStatus status=record(f,'W',8,address,value);
    if (status==PCM_OK) f->memory[address]=value;
    return status;
}
static PcmStatus write16(void *context,uint16_t address,uint16_t value)
{
    Fixture *f=context;
    PcmStatus status=record(f,'W',16,address,value);
    if (status==PCM_OK) {
        f->memory[address]=(uint8_t)(value>>8);
        f->memory[(uint16_t)(address+1u)]=(uint8_t)value;
    }
    return status;
}
static PcmStatus mask_irq(void *context,bool masked)
{
    Fixture *f=context;
    PcmStatus status=record(f,'M',0,0,masked?1:0);
    if (status==PCM_OK) f->irq_masked=masked;
    return status;
}
static void init(Fixture *f,Pcm *pcm,unsigned mode)
{
    memset(f,0,sizeof(*f));memset(pcm,0,sizeof(*pcm));
    f->platform.context=f;f->platform.read8=read8;f->platform.read16=read16;
    f->platform.write8=write8;f->platform.write16=write16;f->platform.mask_irq=mask_irq;
    pcm->platform=&f->platform;pcm->unresolved_task=PCM_TASK_COUNT;
    f->memory[0x0004]=f->memory[0x0019]=0xff;
    f->memory[0x0051]=f->memory[0x0086]=f->memory[0x004f]=0xff;
    f->memory[0x0046]=f->memory[0x003e]=0xff;
    f->memory[0x0044]=(mode==3||mode==4)?0:0x18;
    f->memory[0x027f]=mode==0?7:mode==1?8:mode==2?16:9;
    f->memory[0x400a]=16;
    f->memory[0x0223]=0x9f;f->memory[0x027d]=0x88;
    if (mode==4) f->memory[0x0051]&=(uint8_t)~0x08u;
}
static void test_mode(unsigned mode,PcmStatus expected)
{
    static Fixture f,baseline;Pcm pcm;
    init(&f,&pcm,mode);
    CHECK(pcm_fuel_ignition_precheck(&pcm)==expected);
    if (mode==0) {
        CHECK(f.used==4 && f.memory[0x027f]==8);
        CHECK(f.memory[0x0004]==0xff && f.memory[PCM_COPRST]==0x55);
    } else if (mode==1) {
        CHECK(f.memory[0x0004]==0x74 && f.memory[0x0019]==0x9f);
        CHECK(f.memory[0x027f]==9 && f.memory[0x004f]==0x6f);
        CHECK(f.memory[0x0051]==0xff && f.memory[PCM_COPRST]==0x55);
    } else if (mode==2) {
        CHECK(f.irq_masked && f.memory[0x3039]==8);
        CHECK(f.memory[PCM_COPRST]==0 && f.memory[0x027f]==16);
    } else if (mode==3) {
        CHECK(f.memory[0x027e]==0 && f.memory[0x027f]==0);
        CHECK(f.memory[0x0051]==0xf7 && f.memory[0x0046]==0x7f);
        CHECK(f.memory[0x0044]==0 && f.memory[0x003e]==0xf7);
        CHECK(f.memory[0x0223]==0 && f.memory[0x027d]==0);
    } else {
        CHECK(f.memory[0x0223]==0x9f && f.memory[0x027d]==0x88);
        CHECK(f.memory[0x027f]==0 && f.memory[0x0051]==0xf7);
    }
    baseline=f;
    for (unsigned stop=1;stop<=baseline.used;++stop) {
        init(&f,&pcm,mode);f.fail_at=stop;
        CHECK(pcm_fuel_ignition_precheck(&pcm)==PCM_NO_HARDWARE);
        CHECK(f.used==stop-1 && f.attempts==stop);
        for (unsigned i=0;i<f.used;++i) {
            CHECK(f.events[i].kind==baseline.events[i].kind);
            CHECK(f.events[i].width==baseline.events[i].width);
            CHECK(f.events[i].address==baseline.events[i].address);
            CHECK(f.events[i].value==baseline.events[i].value);
        }
    }
    printf("Ignition precheck mode %u: %u failure-prefix checks.\n",mode,baseline.used);
}
int main(int argc,char **argv)
{
    if (argc==2 && strcmp(argv[1],"--contracts")!=0) return 2;
    CHECK(pcm_fuel_ignition_precheck(NULL)==PCM_BAD_CONFIGURATION);
    test_mode(0,PCM_OK);test_mode(1,PCM_OK);test_mode(2,PCM_HALT_BOUNDARY);
    test_mode(3,PCM_OK);test_mode(4,PCM_OK);
    puts("Ignition/run counter, trap and watchdog prefix contracts passed.");
    return 0;
}
