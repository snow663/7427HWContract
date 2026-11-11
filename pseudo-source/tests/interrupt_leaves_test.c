#define PCM_BOOT_FIXTURE_ENTRY inherited_interrupt_boot_main
#include "boot_system_test.c"
#undef PCM_BOOT_FIXTURE_ENTRY
#include "interrupts.h"

static void interrupt_transfer(Pcm *pcm,uint8_t *memory,bool load)
{
    static const Mapping extra[]={
        {0,0,1,1,offsetof(Pcm,scheduler.timer_seen)},
        {0,7,0xfe,1,offsetof(Pcm,system.interrupt_flags)},
    };
    transfer(pcm,memory,extra,1,load);
    volatile uint8_t *flags=&pcm->system.interrupt_flags;
    if (load) *flags=memory[0]&0xfeu;
    else memory[0]=(uint8_t)((memory[0]&1u)|(*flags&0xfeu));
}
static PcmStatus interrupt_read8(void *v,uint16_t address,uint8_t *out)
{
    BootFixture *f=v;PcmStatus status=boot_read8(v,address,out);
    if (status!=PCM_OK) return status;
    uint16_t frame=word(f->memory,0x900);
    if (f->action==50 && address==0) f->memory[frame]=0x80;
    if (f->action==51 && address==frame) f->memory[frame]=0xaa;
    if (f->action==52 && address==0) { f->memory[0]^=0x55;boot_transfer(f,true); }
    return PCM_OK;
}
static PcmStatus interrupt_write8(void *v,uint16_t address,uint8_t value)
{
    BootFixture *f=v;uint8_t old=f->memory[address];PcmStatus status=boot_write8(v,address,value);
    if (status==PCM_OK && (address==0x3023 || address==0x3025)) f->memory[address]=(uint8_t)(old&~value);
    return status;
}
static PcmStatus interrupt_execute(unsigned mode,BootFixture *f)
{
    Pcm *pcm=f->pcm;
    switch (mode) {
    case 0:return pcm_swi_irq(pcm);
    case 1:return pcm_illegal_trap(pcm);
    case 2:return pcm_cop_reset(pcm);
    case 3:return pcm_clock_failure(pcm);
    case 4:return pcm_external_reset(pcm);
    case 5:return pcm_xirq_irq(pcm,word(f->memory,0x900));
    case 6:return pcm_factory_reference_irq(pcm);
    case 7:return pcm_timer_fallback_irq(pcm);
    case 8:return pcm_overflow_fallback_irq(pcm);
    case 9:return pcm_spi_irq(pcm);
    case 10:return pcm_reference_irq(pcm);
    case 11:case 12: {
        PcmStatus status=mode==11?pcm_external_reset(pcm):pcm_cop_reset(pcm);
        return status==PCM_RESET_BOUNDARY?pcm_boot_retained_validate(pcm):status;
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
        boot_init(&f,&pcm);f.extra_transfer=interrupt_transfer;f.platform.read8=interrupt_read8;
        f.platform.write8=interrupt_write8;pcm.calibration=&pcm_reference_scheduler_calibration;
        if (contracts) {
            CHECK(pcm_spi_irq(NULL)==PCM_OK);
            pcm.scheduler.timer_seen=true;pcm.system.interrupt_flags=0x40;
            CHECK(pcm_cop_reset(&pcm)==PCM_RESET_BOUNDARY && pcm.system.interrupt_flags==0x60 && pcm.scheduler.timer_seen);
            f.platform.write8=NULL;CHECK(pcm_external_reset(&pcm)==PCM_NO_HARDWARE && pcm.system.interrupt_flags==0x60);
            f.platform.read8=NULL;CHECK(pcm_swi_irq(&pcm)==PCM_NO_HARDWARE);
            puts("Distinct halt/reset dispositions, shared cause/timer owner and failed-write prefix contracts pass.");return 0;
        }
        CHECK(mode<13 && count<8192);
        for (unsigned i=0;i<count;++i) { unsigned a,v;CHECK(scanf("%u %u",&a,&v)==2 && a<65536 && v<256);f.memory[a]=(uint8_t)v; }
        boot_transfer(&f,true);f.fail=fail;f.action=action;f.masked=masked!=0;
        PcmStatus status=interrupt_execute(mode,&f);boot_transfer(&f,false);
        printf("{\"status\":%u,\"value\":0,\"state\":\"",(unsigned)status);
        for (unsigned a=0;a<0x900;++a) printf("%02x",mode>=11 && a>=0x3f0 && a<0x400?0:f.memory[a]);
        hex(f.memory,0x3000,0x3070);hex(f.memory,0x3fc0,0x3ffe);printf("\",\"events\":[");
        for (unsigned i=0;i<f.used;++i) { BootEvent *e=&f.events[i];printf("%s[\"%c\",%u,%u,%u,%u]",i?",":"",e->kind,e->width,e->address,e->value,(unsigned)e->masked); }
        puts("]}");
    }
    return 0;
}
