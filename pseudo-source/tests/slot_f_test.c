#define PCM_SLOW_TEST_MAIN inherited_slow_main
#include "slow_fuel_test.c"
#undef PCM_SLOW_TEST_MAIN

static void slot_f_transfer(Pcm *pcm,uint8_t *memory,bool load)
{
    static const Mapping extra[]={
        {0x3b,0,4,1,offsetof(Pcm,runtime.monitor_freeze)},
        {0xd9,8,0,1,offsetof(Pcm,transmission.selected_gear)},
        {0x4c,8,0,1,offsetof(Pcm,transmission.output_shadow)},
        {0x99,8,0,1,offsetof(Pcm,transmission.inhibit_flags)},
        {0x1c,8,0,1,offsetof(Pcm,transmission.fault_flags_primary)},
        {0x1d,8,0,1,offsetof(Pcm,transmission.fault_flags_secondary)},
        {0x86,0,1,1,offsetof(Pcm,transmission.driver_inhibit)},
        {0x8e,8,0,1,offsetof(Pcm,transmission.output_fault_flags)},
        {0x39a,8,0,1,offsetof(Pcm,transmission.current_service_enable)},
        {0x39b,8,0,1,offsetof(Pcm,transmission.current_service_value)},
        {0x8a,8,0,1,offsetof(Pcm,transmission.tcc_flags)},
        {0x8b,8,0,1,offsetof(Pcm,transmission.tcc_state)},
        {0x126,16,0,1,offsetof(Pcm,transmission.tcc_command)},
        {0x12b,16,0,1,offsetof(Pcm,transmission.tcc_lower_limit)},
    };
    slow_transfer(pcm,memory,load);transfer(pcm,memory,extra,SIZE(extra),load);
}
static PcmStatus slot_f_read8(void *v,uint16_t a,uint8_t *out)
{
    Fixture *f=v;PcmStatus status=slow_read8(v,a,out);if (status!=PCM_OK) return status;
    if (f->action==50 && a==0xd7) f->memory[a]^=0x7f;
    if (f->action==51 && a>=0x94 && a<=0x96) f->memory[a]^=0xf0;
    if (f->action==52 && a>=0x5b53 && a<=0x5bc0) f->memory[a]=(uint8_t)(*out+17u);
    if (f->action==55 && a==0x1c) f->memory[a]^=1;
    if (f->action==56 && a>=0x166 && a<=0x185) f->memory[a]=(uint8_t)(*out+17u);
    controller_transfer(f,true);return PCM_OK;
}
static PcmStatus slot_f_read16(void *v,uint16_t a,uint16_t *out)
{
    Fixture *f=v;PcmStatus status=slow_read16(v,a,out);if (status!=PCM_OK) return status;
    if (f->action==53 && (a==0xeb || a==0xf9)) { f->memory[a]^=0x80;f->memory[a+1]^=0xff; }
    controller_transfer(f,true);return PCM_OK;
}
static PcmStatus slot_f_write8(void *v,uint16_t a,uint8_t value)
{
    Fixture *f=v;PcmStatus status=slow_write8(v,a,value);
    if (status==PCM_OK && f->action==54 && a==0x1c) { f->memory[0x3b]^=4;controller_transfer(f,true); }
    return status;
}
static void slot_f_init(Fixture *f,Pcm *pcm,Profiles *p,PcmTransmissionCalibration *transmission)
{
    slow_init(f,pcm,p);*transmission=pcm_reference_transmission_calibration;
    transmission->gear_patterns=f->memory+0xb319;transmission->gear_pattern_length=256;
    p->root.transmission=transmission;f->extra_transfer=slot_f_transfer;
    f->platform.read8=slot_f_read8;f->platform.read16=slot_f_read16;f->platform.write8=slot_f_write8;
    f->platform.task[PCM_SLOT_0F]=NULL;
}
static PcmStatus slot_f_execute(unsigned mode,Fixture *f)
{
    Pcm *pcm=f->pcm;PcmStatus status;
#define RUN(call) do { status=(call);if (status!=PCM_OK) return status; } while (0)
    switch (mode) {
    case 0:return pcm_diagnostic_brake_set(pcm);
    case 1:return pcm_diagnostic_brake_clear(pcm);
    case 2:return pcm_diagnostic_tcc_slip(pcm);
    case 3:return pcm_diagnostic_top_gear_slip(pcm);
    case 4:return pcm_diagnostic_tcc_released_slip(pcm);
    case 5:return pcm_diagnostic_current_error(pcm);
    case 6:return pcm_diagnostic_transmission_temperature(pcm);
    case 7:return pcm_diagnostic_ratio_invalid(pcm);
    case 8:return pcm_diagnostic_ratio_lowgear(pcm);
    case 9:return pcm_diagnostic_ratio_highgear(pcm);
    case 10:return pcm_diagnostic_slot_f(pcm);
    case 11:return pcm_slot_0f(pcm);
    case 12:RUN(pcm_slot_01(pcm));RUN(pcm_slot_0f(pcm));RUN(pcm_fuel_control(pcm));return pcm_reference_event(pcm);
    case 13:RUN(pcm_slot_0f(pcm));return pcm_fuel_control(pcm);
    default:RUN(pcm_slot_0f(pcm));return pcm_slot_0f(pcm);
    }
#undef RUN
}
static void slot_f_contracts(void)
{
    static Fixture f;Pcm pcm;Profiles p;PcmTransmissionCalibration t;
    slot_f_init(&f,&pcm,&p,&t);pcm.runtime.monitor_freeze=true;
    CHECK(pcm_diagnostic_slot_f(&pcm)==PCM_OK && f.used==0);
    slot_f_init(&f,&pcm,&p,&t);p.root.transmission=NULL;
    CHECK(pcm_slot_0f(&pcm)==PCM_BAD_CONFIGURATION && f.used==0 && !pcm.runtime.refresh_requested);
    slot_f_init(&f,&pcm,&p,&t);controller_transfer(&f,true);f.fail_at=1;
    CHECK(pcm_slot_0f(&pcm)==PCM_NO_HARDWARE && !pcm.runtime.refresh_requested);
    slot_f_init(&f,&pcm,&p,&t);controller_transfer(&f,true);
    CHECK(pcm_slot_0f(&pcm)==PCM_OK && pcm.runtime.refresh_requested);
    puts("SlotF freeze, resident root, absent transmission profile and failed-prefix refresh contracts pass.");
}
int main(int argc,char **argv)
{
    const char *path=getenv("PCM_FUEL_CONTROLLER_ROM");CHECK(path!=NULL || argc==2);
    if (path!=NULL) { FILE *file=fopen(path,"rb");CHECK(file!=NULL && fread(stock,1,sizeof(stock),file)==sizeof(stock));CHECK(fclose(file)==0); }
    if (argc==2 && strcmp(argv[1],"--contracts")==0) { slot_f_contracts();return 0; }
    if (argc==2) return inherited_slow_main(argc,argv);
    static Fixture f;Pcm pcm;Profiles p;PcmTransmissionCalibration t;unsigned mode,fail,action,masked,count;
    while (scanf("%u %u %u %u %u",&mode,&fail,&action,&masked,&count)==5) {
        CHECK(mode<15 && count<4096);slot_f_init(&f,&pcm,&p,&t);
        for (unsigned i=0;i<count;++i) { unsigned a,byte;CHECK(scanf("%u %u",&a,&byte)==2 && a<65536 && byte<256);f.memory[a]=(uint8_t)byte; }
        controller_profile(&f,&p);controller_transfer(&f,true);f.fail_at=fail;f.action=action;f.masked=masked!=0;
        if (f.memory[0x913]) f.platform.task[PCM_AFR_EXTENSION]=mixture_extension;
        if (f.memory[0x920]) f.platform.task[PCM_GOVERNOR_EXTENSION]=governor_extension;
        PcmStatus status=slot_f_execute(mode,&f);controller_transfer(&f,false);
        unsigned unresolved=pcm.unresolved_task==PCM_AFR_EXTENSION?1:pcm.unresolved_task==PCM_GOVERNOR_EXTENSION?2:0;
        printf("{\"status\":%u,\"value\":0,\"unresolved\":%u,\"masked\":%u,\"state\":\"",(unsigned)status,unresolved,(unsigned)f.masked);
        for (unsigned a=0;a<0x900;++a) printf("%02x",a>=0x3b0 && a<0x400?0:f.memory[a]);
        for (unsigned a=0x3000;a<0x3070;++a) printf("%02x",f.memory[a]);
        for (unsigned a=0x3fc0;a<0x3ffe;++a) printf("%02x",f.memory[a]);
        printf("\",\"events\":[");
        for (unsigned i=0;i<f.used;++i) { Event *e=&f.events[i];printf("%s[\"%c\",%u,%u,%u,%u]",i?",":"",e->kind,e->width,e->address,e->value,(unsigned)e->masked); }
        puts("]}");
    }
    return 0;
}
