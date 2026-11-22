#define PCM_CONTROLLER_TEST_MAIN inherited_controller_main
#include "fuel_controller_test.c"
#undef PCM_CONTROLLER_TEST_MAIN
#include "scheduler.h"

static void slow_transfer(Pcm *pcm,uint8_t *memory,bool load)
{
    static const Mapping extra[]={
        {0x51,0,4,1,offsetof(Pcm,runtime.refresh_requested)},
        {0x50,0,0x10,1,offsetof(Pcm,runtime.diagnostic_switch)},
    };
    transfer(pcm,memory,extra,SIZE(extra),load);
}
static PcmStatus slow_read8(void *v,uint16_t a,uint8_t *out)
{
    Fixture *f=v;PcmStatus status=controller_read8(v,a,out);if (status!=PCM_OK) return status;
    if (f->action==40 && a==0x89) f->memory[a]^=0x20;
    if (f->action==41 && a==0x5d0a) f->memory[a]=(uint8_t)(*out+37u);
    if (f->action==43 && a==0xa7) f->memory[2]^=0x10;
    if (f->action==44 && a==0x2f3) f->memory[a]=(uint8_t)(*out+17u);
    if (f->action==45 && a>=0x5b2b && a<=0x5b3c) f->memory[a]^=0xff;
    if (f->action==46 && a==0x22a) f->memory[a]=(uint8_t)(*out+17u);
    if (f->action==48 && a==0x72) f->memory[a]^=3;
    controller_transfer(f,true);return PCM_OK;
}
static PcmStatus slow_read16(void *v,uint16_t a,uint16_t *out)
{
    Fixture *f=v;PcmStatus status=controller_read16(v,a,out);if (status!=PCM_OK) return status;
    if (f->action==42 && a>=0x5168 && a<0x5190) f->memory[a]=(uint8_t)(f->memory[a]+17u);
    controller_transfer(f,true);return PCM_OK;
}
static PcmStatus slow_write8(void *v,uint16_t a,uint8_t value)
{
    Fixture *f=v;PcmStatus status=controller_write8(v,a,value);
    if (status==PCM_OK && f->action==47 && (a==0x98 || a==0x99)) { f->memory[2]^=0x10;controller_transfer(f,true); }
    return status;
}
static void slow_init(Fixture *f,Pcm *pcm,Profiles *p)
{
    controller_init(f,pcm,p);f->extra_transfer=slow_transfer;
    f->platform.read8=slow_read8;f->platform.read16=slow_read16;f->platform.write8=slow_write8;
}
static PcmStatus slow_execute(unsigned mode,Fixture *f,uint8_t *value)
{
    Pcm *pcm=f->pcm;PcmStatus status;
#define RUN(call) do { status=(call);if (status!=PCM_OK) return status; } while (0)
    switch (mode) {
    case 0:return pcm_transmission_baro(pcm);
    case 1:return pcm_tcc_nonelectronic(pcm);
    case 2:return pcm_slot_01(pcm);
    case 3:return pcm_pump_feedback(pcm);
    case 4:return pcm_fuel_slow(pcm);
    case 5:return pcm_fault_primary_reaction(pcm);
    case 6:return pcm_fault_reaction_mask(pcm,word(f->memory,0x930),value);
    case 7:return pcm_fault_injection_reaction(pcm);
    case 8:return pcm_slot_0f_finish(pcm);
    case 9:RUN(pcm_slot_01(pcm));return pcm_fuel_control(pcm);
    case 10:RUN(pcm_slot_0f_finish(pcm));return pcm_fuel_control(pcm);
    default:RUN(pcm_slot_01(pcm));RUN(pcm_slot_0f_finish(pcm));RUN(pcm_fuel_control(pcm));return pcm_reference_event(pcm);
    }
#undef RUN
}
static void slow_contracts(void)
{
    static Fixture f;Pcm pcm;Profiles p;uint8_t value=77;
    slow_init(&f,&pcm,&p);CHECK(pcm_fault_reaction_mask(&pcm,0,NULL)==PCM_BAD_CONFIGURATION && f.used==0);
    f.fail_at=1;CHECK(pcm_fault_reaction_mask(&pcm,0xe755,&value)==PCM_NO_HARDWARE && value==77);
    slow_init(&f,&pcm,&p);f.memory[0x1e]=f.memory[0x5b3c]=f.memory[0x5b33]=0x80;
    f.memory[0xe71f]=f.memory[0xe75e]=0x80;f.memory[0x98]=0xa5;f.memory[0x99]=0x55;
    controller_transfer(&f,true);
    CHECK(pcm_fault_primary_reaction(&pcm)==PCM_OK && f.memory[0x98]==0xad);
    CHECK(pcm_fault_injection_reaction(&pcm)==PCM_OK && f.memory[0x99]==0x45);
    f.memory[0x5b3c]=0;
    CHECK(pcm_fault_primary_reaction(&pcm)==PCM_OK && f.memory[0x98]==0xa5);
    CHECK(pcm_fault_injection_reaction(&pcm)==PCM_OK && f.memory[0x99]==0x55);
    slow_init(&f,&pcm,&p);pcm.scheduler.phase=0x1f;pcm.fuel.startup_hold=77;
    CHECK(pcm_fuel_slow(&pcm)==PCM_OK && pcm.fuel.startup_hold==77 && pcm.fuel.charge_temperature>=29824u);
    CHECK(pcm_slot_0f_finish(&pcm)==PCM_OK && pcm.runtime.refresh_requested);
    slow_init(&f,&pcm,&p);f.fail_at=1;
    CHECK(pcm_slot_0f_finish(&pcm)==PCM_NO_HARDWARE && !pcm.runtime.refresh_requested);
    slow_init(&f,&pcm,&p);p.root.air=NULL;
    CHECK(pcm_slot_01(&pcm)==PCM_BAD_CONFIGURATION && f.used==0);
    puts("Fault-mask output retention/polarity, slow phase admission, suffix refresh and slot1 prefix-stop contracts pass.");
}
#ifndef PCM_SLOW_TEST_MAIN
#define PCM_SLOW_TEST_MAIN main
#endif
int PCM_SLOW_TEST_MAIN(int argc,char **argv)
{
    const char *path=getenv("PCM_FUEL_CONTROLLER_ROM");CHECK(path!=NULL || argc==2);
    if (path!=NULL) { FILE *file=fopen(path,"rb");CHECK(file!=NULL && fread(stock,1,sizeof(stock),file)==sizeof(stock));CHECK(fclose(file)==0); }
    if (argc==2 && strcmp(argv[1],"--contracts")==0) { slow_contracts();return 0; }
    if (argc==2) return inherited_controller_main(argc,argv);
    static Fixture f;Pcm pcm;Profiles p;unsigned mode,fail,action,masked,count;
    while (scanf("%u %u %u %u %u",&mode,&fail,&action,&masked,&count)==5) {
        CHECK(mode<12 && count<4096);slow_init(&f,&pcm,&p);
        for (unsigned i=0;i<count;++i) { unsigned a,byte;CHECK(scanf("%u %u",&a,&byte)==2 && a<65536 && byte<256);f.memory[a]=(uint8_t)byte; }
        controller_profile(&f,&p);controller_transfer(&f,true);f.fail_at=fail;f.action=action;f.masked=masked!=0;
        if (f.memory[0x913]) f.platform.task[PCM_AFR_EXTENSION]=mixture_extension;
        if (f.memory[0x920]) f.platform.task[PCM_GOVERNOR_EXTENSION]=governor_extension;
        uint8_t value=0;PcmStatus status=slow_execute(mode,&f,&value);controller_transfer(&f,false);
        unsigned unresolved=pcm.unresolved_task==PCM_AFR_EXTENSION?1:pcm.unresolved_task==PCM_GOVERNOR_EXTENSION?2:0;
        printf("{\"status\":%u,\"value\":%u,\"unresolved\":%u,\"masked\":%u,\"state\":\"",(unsigned)status,(unsigned)value,unresolved,(unsigned)f.masked);
        for (unsigned a=0;a<0x900;++a) printf("%02x",a>=0x3b0 && a<0x400?0:f.memory[a]);
        for (unsigned a=0x3000;a<0x3070;++a) printf("%02x",f.memory[a]);
        for (unsigned a=0x3fc0;a<0x3ffe;++a) printf("%02x",f.memory[a]);
        printf("\",\"events\":[");
        for (unsigned i=0;i<f.used;++i) { Event *e=&f.events[i];printf("%s[\"%c\",%u,%u,%u,%u]",i?",":"",e->kind,e->width,e->address,e->value,(unsigned)e->masked); }
        puts("]}");
    }
    return 0;
}
