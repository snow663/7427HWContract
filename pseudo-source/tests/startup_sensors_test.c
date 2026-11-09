#define main inherited_fuel_main
#include "fuel_output_test.c"
#undef main
#include "startup.h"
#include "system.h"

static const Mapping startup_state_map[]={
    {1,8,0,1,offsetof(Pcm,system.factory_flags)},
    {2,8,0,1,offsetof(Pcm,scheduler.phase)},
    {0,0,1,1,offsetof(Pcm,scheduler.timer_seen)},
    {0x50,0,8,1,offsetof(Pcm,io.diagnostic_warm)},
};
static PcmStatus startup_execute(unsigned mode,Pcm *pcm)
{
    if (mode==0) return pcm_factory_admit(pcm);
    if (mode==1) return pcm_reset_sensors(pcm);
    if (mode==2) return pcm_periodic_irq(pcm);
    PcmStatus r=pcm_reset_sensors(pcm);if (r!=PCM_OK) return r;
    return pcm->runtime.factory_mode?pcm_periodic_irq(pcm):PCM_OK;
}
static void startup_sensor_contracts(void)
{
    static Fixture f;Pcm pcm;PcmCalibration root;PcmFuelCalibration fuel;PcmIacCalibration iac;
#define INIT() init(&f,&pcm,&root,&fuel,&iac)
    INIT();pcm.io.diagnostic_sample=40;pcm.fuel.raw_throttle=251;
    CHECK(pcm_factory_admit(&pcm)==PCM_OK && pcm.io.diagnostic_warm && !pcm.runtime.factory_mode && f.used==0);
    INIT();pcm.io.diagnostic_sample=100;pcm.io.diagnostic_warm=true;pcm.system.factory_flags=0xff;
    CHECK(pcm_factory_admit(&pcm)==PCM_OK && pcm.io.diagnostic_warm && pcm.system.factory_flags==0xff);
    INIT();pcm.io.diagnostic_sample=40;pcm.fuel.raw_throttle=252;pcm.io.raw_coolant=252;pcm.io.auxiliary_reference=5;
    f.fail_at=1;pcm.system.factory_flags=0xff;
    CHECK(pcm_factory_admit(&pcm)==PCM_NO_HARDWARE && pcm.runtime.factory_mode && pcm.io.diagnostic_warm && pcm.system.factory_flags==0);
    INIT();pcm.runtime.factory_mode=true;pcm.scheduler.phase=255;f.masked=true;
    CHECK(pcm_periodic_irq(&pcm)==PCM_FACTORY_BOUNDARY && pcm.scheduler.phase==0 && pcm.scheduler.timer_seen && f.masked);
    INIT();f.platform.read8=NULL;
    CHECK(pcm_reset_sensors(&pcm)==PCM_NO_HARDWARE && f.used==0);
#undef INIT
    puts("Factory window partial latch, failed admission prefix, factory phase wrap and acquisition dependency checks pass.");
}
int main(int argc,char **argv)
{
    if (argc==2 && strcmp(argv[1],"--contracts")==0) { startup_sensor_contracts();return 0; }
    if (argc==2) return inherited_fuel_main(argc,argv);
    static Fixture f;Pcm pcm;PcmCalibration root;PcmFuelCalibration fuel;PcmIacCalibration iac;
    uint16_t outputs[512];unsigned output_count=0;
    for (unsigned a=0;a<0x4000;++a) {
        bool found=(a>=0x3000 && a<0x3035) || (a>=0x3fc0 && a<0x3ffe);
        for (unsigned k=0;k<3;++k) {
            const Mapping *map=k==0?reference_state_map:k==1?fuel_state_map:startup_state_map;
            size_t count=k==0?SIZE(reference_state_map):k==1?SIZE(fuel_state_map):SIZE(startup_state_map);
            for (size_t i=0;i<count;++i) if (a>=map[i].address && a<map[i].address+(map[i].width==16?2u:1u)) found=true;
        }
        if (found) { CHECK(output_count<SIZE(outputs));outputs[output_count++]=(uint16_t)a; }
    }
    unsigned mode,count;
    while (scanf("%u %u",&mode,&count)==2) {
        CHECK(mode<4 && count<2048);init(&f,&pcm,&root,&fuel,&iac);
        for (unsigned i=0;i<count;++i) { unsigned a,v;CHECK(scanf("%u %u",&a,&v)==2 && a<65536 && v<256);f.memory[a]=(uint8_t)v; }
        state_transfer(&pcm,&f,true);transfer(&pcm,f.memory,startup_state_map,SIZE(startup_state_map),true);
        f.fail_at=f.memory[0x907];f.action=f.memory[0x908];f.masked=f.memory[0x909]!=0;
        PcmStatus status=startup_execute(mode,&pcm);
        state_transfer(&pcm,&f,false);transfer(&pcm,f.memory,startup_state_map,SIZE(startup_state_map),false);
        printf("{\"status\":%u,\"masked\":%u,\"state\":[",(unsigned)status,(unsigned)f.masked);
        for (unsigned i=0;i<output_count;++i) printf("%s%u",i?",":"",f.memory[outputs[i]]);
        printf("],\"events\":[");
        for (unsigned i=0;i<f.used;++i) { Event *e=&f.events[i];printf("%s[\"%c\",%u,%u,%u,%u]",i?",":"",e->kind,e->width,e->address,e->value,(unsigned)e->masked); }
        puts("]}");
    }
    return 0;
}
