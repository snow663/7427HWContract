#define PCM_BOOT_FIXTURE_ENTRY inherited_background_boot_main
#include "boot_system_test.c"
#undef PCM_BOOT_FIXTURE_ENTRY
#include "scheduler.h"
#include "serial_fixture_map.h"

static void background_transfer(Pcm *pcm,uint8_t *memory,bool load)
{
    transfer(pcm,memory,serial_state_map,SIZE(serial_state_map),load);
    static const Mapping extra[]={
        {0x029b,16,0,1,offsetof(Pcm,system.refresh_cursor)},
        {0x02d1,16,0,1,offsetof(Pcm,system.stack_watermark)},
        {0x51,0,4,1,offsetof(Pcm,runtime.refresh_requested)},
        {4,0,4,1,offsetof(Pcm,runtime.refresh_late)},
        {2,8,0,1,offsetof(Pcm,scheduler.phase)},
        {0x248,8,0,1,offsetof(Pcm,iac.blm_value)},
        {0x4c,8,0,1,offsetof(Pcm,transmission.output_shadow)},
        {4,0,8,1,offsetof(Pcm,spark.run_transition)},
        {0x3b,0,0x10,1,offsetof(Pcm,runtime.engine_service)},
    };
    transfer(pcm,memory,extra,SIZE(extra),load);
}
static PcmStatus background_read16(void *v,uint16_t address,uint16_t *out)
{
    BootFixture *f=v;PcmStatus status=boot_read16(v,address,out);
    if (status!=PCM_OK) return status;
    if (f->action==40 && address==0x50) f->polls=1; /* Pending IRQ waits for CLI. */
    if (f->action==41 && address==0x800) f->memory[0x800]^=0xa5;
    if ((f->action==44 || f->action==45) && address==0x2d1 && f->polls++==0) {
        f->memory[0x2d1]=3;f->memory[0x2d2]=0xb0;boot_transfer(f,true);
    }
    return PCM_OK;
}
static PcmStatus background_mask(void *v,bool masked)
{
    BootFixture *f=v;PcmStatus status=boot_record(f,'M',0,0,masked);
    if (status!=PCM_OK) return status;
    f->masked=masked;
    if (!masked) {
        boot_transfer(f,false);
        if (f->action==40 && f->polls==1) { f->memory[0x50]|=0x20;f->polls=2; }
        if (f->action==42 && word(f->memory,0x29b)==0x900) { f->memory[0x29c]=0xa5;f->memory[0x51]^=0x80; }
        if (f->action==43 && f->polls++==0) { f->memory[0x29b]=4;f->memory[0x29c]=0; }
        boot_transfer(f,true);
    }
    return PCM_OK;
}
static PcmStatus background_write8(void *v,uint16_t address,uint8_t value)
{
    BootFixture *f=v;uint8_t previous=f->memory[address];PcmStatus status=boot_write8(v,address,value);
    if (status==PCM_OK && address==PCM_TFLG1) f->memory[address]=(uint8_t)(previous&~value);
    return status;
}
static PcmStatus background_slot(Pcm *pcm,PcmTask task)
{
    CHECK(task==PCM_SLOT_0F);return boot_record(pcm->platform->context,'T',0,0x7b5a,0);
}
static PcmStatus background_execute(unsigned mode,Pcm *pcm)
{
    switch (mode) {
    case 0:return pcm_ram_refresh(pcm);
    case 1:return pcm_stack_watermark(pcm);
    case 2:return pcm_background_pass(pcm);
    case 3:return pcm_reset_timers(pcm);
    case 4: {
        PcmStatus status=pcm_slot_0f(pcm);if (status!=PCM_OK) return status;
        status=pcm_slot_0e(pcm);if (status!=PCM_OK) return status;
        return pcm_background_pass(pcm);
    }
    case 5: {
        PcmStatus status=pcm_reset_serial(pcm);if (status!=PCM_OK) return status;
        status=pcm_reset_timers(pcm);if (status!=PCM_OK) return status;
        return pcm_background_pass(pcm);
    }
    default:return PCM_BAD_CONFIGURATION;
    }
}
int main(int argc,char **argv)
{
    const char *path=getenv("PCM_BOOT_ROM");CHECK(path!=NULL || argc==2);
    if (path!=NULL) { FILE *file=fopen(path,"rb");CHECK(file!=NULL && fread(boot_rom,1,65536,file)==65536);CHECK(fclose(file)==0); }
    CHECK(argc==1 || (argc==2 && strcmp(argv[1],"--contracts")==0));
    static BootFixture f;Pcm pcm;unsigned mode,fail,action,masked,count;bool contracts=argc==2;
    while (contracts || scanf("%u %u %u %u %u",&mode,&fail,&action,&masked,&count)==5) {
        boot_init(&f,&pcm);f.extra_transfer=background_transfer;f.platform.read16=background_read16;
        f.platform.mask_irq=background_mask;f.platform.write8=background_write8;
        f.platform.task[PCM_SLOT_0F]=background_slot;pcm.calibration=&pcm_reference_scheduler_calibration;
        if (contracts) {
            CHECK(pcm_stack_watermark(&pcm)==PCM_OK && pcm.system.stack_watermark==0x3ff);
            f.used=f.attempts=0;f.platform.mask_irq=NULL;
            CHECK(pcm_background_pass(&pcm)==PCM_NO_HARDWARE && f.used==1 && pcm.system.stack_watermark==0x3ff);
            f.platform.mask_irq=background_mask;pcm.runtime.refresh_requested=true;pcm.system.refresh_cursor=0x900;
            CHECK(pcm_ram_refresh(&pcm)==PCM_OK && !pcm.runtime.refresh_requested && pcm.system.refresh_cursor==0);
            puts("Foreground stack bounds, missing-mask prefix and canonical refresh completion contracts pass.");return 0;
        }
        CHECK(mode<6 && count<8192);
        for (unsigned i=0;i<count;++i) { unsigned a,v;CHECK(scanf("%u %u",&a,&v)==2 && a<65536 && v<256);f.memory[a]=(uint8_t)v; }
        boot_transfer(&f,true);f.fail=fail;f.action=action;f.masked=masked!=0;
        PcmStatus status=background_execute(mode,&pcm);boot_transfer(&f,false);
        printf("{\"status\":%u,\"value\":0,\"state\":\"",(unsigned)status);
        for (unsigned a=0;a<0x900;++a) printf("%02x",mode>=4 && a>=0x3f0 && a<0x400?0:f.memory[a]);
        hex(f.memory,0x3000,0x3070);hex(f.memory,0x3fc0,0x3ffe);printf("\",\"events\":[");
        for (unsigned i=0;i<f.used;++i) { BootEvent *e=&f.events[i];printf("%s[\"%c\",%u,%u,%u,%u]",i?",":"",e->kind,e->width,e->address,e->value,(unsigned)e->masked); }
        puts("]}");
    }
    return 0;
}
