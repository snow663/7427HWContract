#define PCM_BOOT_FIXTURE_ENTRY inherited_factory_boot_main
#include "boot_system_test.c"
#undef PCM_BOOT_FIXTURE_ENTRY
#include "scheduler.h"
#include "serial.h"
#include "serial_fixture_map.h"

static void factory_transfer(Pcm *pcm,uint8_t *memory,bool load)
{
    transfer(pcm,memory,serial_state_map,SIZE(serial_state_map),load);
    static const Mapping extra[]={
        {2,8,0,1,offsetof(Pcm,scheduler.phase)},
        {0,0,1,1,offsetof(Pcm,scheduler.timer_seen)},
        {0x1a,0,2,1,offsetof(Pcm,runtime.adc_timeout)},
        {0x3b,0,0x10,1,offsetof(Pcm,runtime.engine_service)},
    };
    transfer(pcm,memory,extra,SIZE(extra),load);
}
static PcmStatus factory_read8(void *v,uint16_t address,uint8_t *out)
{
    BootFixture *f=v;boot_transfer(f,false);uint8_t sample=f->memory[address];
    if (address==PCM_ADCTL) sample=(uint8_t)((sample&0x7fu)|(f->polls>=f->memory[f->memory[PCM_ADCTL]==3?0x901:0x900]?0x80:0));
    if (address==PCM_ADR1) sample=f->memory[f->memory[PCM_ADCTL]==3?0x903:0x902];
    PcmStatus status=boot_record(f,'R',8,address,sample);if (status!=PCM_OK) return status;*out=sample;
    if (address==PCM_ADCTL) ++f->polls;
    if (f->action==30 && address==PCM_PORTD) f->memory[address]^=0xc7;
    if (f->action==31 && address==PCM_BOARD_HEARTBEAT) { f->memory[0x364]=2;boot_transfer(f,true); }
    if (f->action==33 && address==0x392) f->memory[0x393]^=0xff;
    return PCM_OK;
}
static PcmStatus factory_write8(void *v,uint16_t address,uint8_t value)
{
    BootFixture *f=v;uint8_t previous=f->memory[address];PcmStatus status=boot_write8(v,address,value);
    if (status!=PCM_OK) return status;
    if (address==PCM_ADCTL) f->polls=0;
    if (address==PCM_TFLG1) f->memory[address]=(uint8_t)(previous&~value);
    if (f->action==32 && address==PCM_SCDR) { f->pcm->serial.checksum=7;f->pcm->serial.count=254; }
    return PCM_OK;
}
static PcmStatus factory_mask(void *v,bool masked)
{
    BootFixture *f=v;PcmStatus status=boot_record(f,'M',0,0,masked);
    if (status==PCM_OK) f->masked=masked;
    return status;
}
static PcmStatus factory_entry(Pcm *pcm,PcmTask task)
{
    BootFixture *f=pcm->platform->context;CHECK(task==PCM_FACTORY_ENTRY);
    PcmStatus status=boot_record(f,'T',0,0xfa5b,0);
    return status!=PCM_OK?status:f->action==37?PCM_STACK_BOUNDARY:PCM_OK;
}
static PcmStatus factory_call_address(void *v,uint16_t address)
{
    BootFixture *f=v;PcmStatus status=boot_record(f,'C',0,address,0);
    if (status!=PCM_OK) return status;
    if (f->action==34) {
        f->pcm->serial.last_id=3;f->pcm->system.factory_flags^=0xa5;
        boot_transfer(f,false);
        f->memory[0x390]^=0xff;f->memory[0x3ffc]^=0x55;boot_transfer(f,true);
    }
    return f->action==35?PCM_TRAP_BOUNDARY:PCM_OK;
}
static PcmStatus factory_execute(unsigned mode,BootFixture *f)
{
    switch (mode) {
    case 0:return pcm_factory_cycle(f->pcm);
    case 1: {
        PcmStatus status=pcm_periodic_irq(f->pcm);
        return status==PCM_FACTORY_BOUNDARY?pcm_factory_cycle(f->pcm):status;
    }
    case 2:return pcm_factory_upload(f->pcm);
    case 3:return pcm_factory_call(f->pcm);
    case 4:return pcm_factory_outputs(f->pcm,f->memory[0x904]);
    case 5: {
        PcmStatus status=pcm_serial_accept(f->pcm,f->pcm->serial.descriptor);
        return status==PCM_OK?pcm_factory_cycle(f->pcm):status;
    }
    default:return PCM_BAD_CONFIGURATION;
    }
}
int main(int argc,char **argv)
{
    const char *path=getenv("PCM_BOOT_ROM");CHECK(path!=NULL || argc==2);
    if (path!=NULL) { FILE *file=fopen(path,"rb");CHECK(file!=NULL && fread(boot_rom,1,65536,file)==65536);CHECK(fclose(file)==0); }
    CHECK(argc==1 || (argc==2 && strcmp(argv[1],"--contracts")==0));
    static BootFixture f;Pcm pcm;unsigned mode,fail,action,masked,count;
    bool contracts=argc==2;
    while (contracts || scanf("%u %u %u %u %u",&mode,&fail,&action,&masked,&count)==5) {
        boot_init(&f,&pcm);f.extra_transfer=factory_transfer;
        f.platform.read8=factory_read8;f.platform.write8=factory_write8;f.platform.mask_irq=factory_mask;
        f.platform.task[PCM_FACTORY_ENTRY]=factory_entry;f.platform.call_address=factory_call_address;
        pcm.calibration=&pcm_reference_scheduler_calibration;
        if (contracts) {
            f.platform.task[PCM_FACTORY_ENTRY]=NULL;
            CHECK(pcm_factory_cycle(&pcm)==PCM_UNIMPLEMENTED && f.used==0 && pcm.unresolved_task==PCM_FACTORY_ENTRY);
            f.platform.call_address=NULL;
            CHECK(pcm_factory_call(&pcm)==PCM_NO_HARDWARE && (pcm.system.factory_flags&1u));
            puts("Factory entry precondition, unresolved callback and arm-before-dispatch contracts pass.");return 0;
        }
        CHECK(mode<6 && count<4096);
        for (unsigned i=0;i<count;++i) { unsigned a,v;CHECK(scanf("%u %u",&a,&v)==2 && a<65536 && v<256);f.memory[a]=(uint8_t)v; }
        boot_transfer(&f,true);f.fail=fail;f.action=action;f.masked=masked!=0;
        if (action==38) f.platform.call_address=NULL;
        if (action==39) f.platform.task[PCM_FACTORY_ENTRY]=NULL;
        PcmStatus status=factory_execute(mode,&f);boot_transfer(&f,false);
        printf("{\"status\":%u,\"value\":0,\"state\":\"",(unsigned)status);
        for (unsigned a=0;a<0x900;++a) printf("%02x",a>=0x3b0 && a<0x400?0:f.memory[a]);
        hex(f.memory,0x3000,0x3070);hex(f.memory,0x3fc0,0x3ffe);printf("\",\"events\":[");
        for (unsigned i=0;i<f.used;++i) { BootEvent *e=&f.events[i];printf("%s[\"%c\",%u,%u,%u,%u]",i?",":"",e->kind,e->width,e->address,e->value,(unsigned)e->masked); }
        puts("]}");
    }
    return 0;
}
