/* Connected $7D4B..$8547 contract using the existing, fully calibrated
 * fuel-delivery host fixture. Its 64K memory is TEST backing only.
 * The real address API resolves canonical RAM via explicit opt-in.
 * No target firmware or physical injector actuation is inferred. */
#define PCM_DELIVERY_TEST_MAIN inherited_delivery_main
#include "fuel_delivery_test.c"
#undef PCM_DELIVERY_TEST_MAIN

static void cycle_init(Fixture *f,Pcm *pcm,PcmCalibration *root,
                       PcmFuelCalibration *fuel,PcmIacCalibration *iac,
                       PcmAirCalibration *air,PcmIoCalibration *io,
                       PcmMixtureCalibration *mix,PcmFeedbackCalibration *fb,
                       PcmDeliveryCalibration *dl,unsigned phase)
{
    delivery_init(f,pcm,root,fuel,iac,air,io,mix,fb,dl);
    f->platform.bind_fuel_ram_owners=true;
    pcm->scheduler.phase=(uint8_t)phase;
    pcm->system.fuel_ignition_counter=7;
    pcm->reference.latch_inhibited=true;
    pcm->runtime.fuel_running=true;
    pcm->runtime.spark_running=true;
    pcm->fuel.authorized=false;
    pcm->fuel.authorization_capture=0;
    pcm->spark.idle_state=true;
    pcm->spark.map_filtered=100;
    pcm->spark.rpm_high=50;
    pcm->io.map_previous_rpm=49;
    pcm->io.coolant_context=0xa0;
    pcm->fuel.raw_oxygen=128;
    pcm->fuel.raw_throttle=70;
    pcm->iac.tps_zero_high=20;
    pcm->spark.battery_sample=50;
    pcm->reference.coolant=160;
    pcm->reference.battery=128;
    pcm->spark.barometric_pressure=120;
    root->mode_f=0x80;
    root->mode_d=0x40; /* fuel authorization required, no capture yet */
    root->reference.mode_b=0; /* direct zero packet publish */
    f->memory[PCM_TIC2]=0;
    f->memory[PCM_TIC2+1]=0;
    f->memory[0x4009]=0xff;
    f->memory[0x400a]=0xff;
}
static unsigned cycle_injector_writes(const Fixture *f)
{
    unsigned count=0;
    for(unsigned i=0;i<f->used;++i)
        if(f->events[i].kind=='W' && f->events[i].address==PCM_INJECTOR_WORD)
            ++count;
    return count;
}
static void cycle_authorization_zero_packet(void)
{
    static Fixture f;Pcm pcm;PcmCalibration root;PcmFuelCalibration fuel;PcmIacCalibration iac;
    PcmAirCalibration air;PcmIoCalibration io;PcmMixtureCalibration mix;
    PcmFeedbackCalibration fb;PcmDeliveryCalibration dl;
    for(unsigned phase=0;phase<8;++phase) {
        cycle_init(&f,&pcm,&root,&fuel,&iac,&air,&io,&mix,&fb,&dl,phase);
        PcmStatus status=pcm_fuel_cycle(&pcm);
        CHECK(status==PCM_OK);
        CHECK(pcm.system.fuel_ignition_counter==8);
        CHECK(f.memory[0x027e]==0 && f.memory[0x027f]==8);
        CHECK(f.memory[PCM_COPRST]==0x55);
        CHECK(!pcm.fuel.authorized && pcm.reference.delivered_pulse==0);
        CHECK(f.memory[PCM_INJECTOR_WORD]==0 && f.memory[PCM_INJECTOR_WORD+1]==0);
        CHECK(cycle_injector_writes(&f)==1);
        CHECK(pcm.spark.previous_throttle==0);
        CHECK(pcm.reference.throttle!=0);
        CHECK(pcm.spark.density==(uint16_t)((uint32_t)100u*65536u/694u+2649u));
        if((phase&6u)==2u)
            CHECK(pcm.transmission.governor_requested_throttle==255);
    }
}
static void cycle_trap_prevents_delivery(void)
{
    static Fixture f;Pcm pcm;PcmCalibration root;PcmFuelCalibration fuel;PcmIacCalibration iac;
    PcmAirCalibration air;PcmIoCalibration io;PcmMixtureCalibration mix;
    PcmFeedbackCalibration fb;PcmDeliveryCalibration dl;
    cycle_init(&f,&pcm,&root,&fuel,&iac,&air,&io,&mix,&fb,&dl,2);
    pcm.system.fuel_ignition_counter=8;
    f.memory[0x4009]=0;f.memory[0x400a]=8;
    CHECK(pcm_fuel_cycle(&pcm)==PCM_HALT_BOUNDARY);
    CHECK(f.memory[0x3039]==8 && f.masked);
    CHECK(pcm.system.fuel_ignition_counter==8);
    CHECK(!pcm.runtime.fuel_running && !pcm.runtime.spark_running);
    CHECK(cycle_injector_writes(&f)==0);
    CHECK(f.memory[PCM_COPRST]==0);
}
static void cycle_provider_failure_prefix(void)
{
    static Fixture f;Pcm pcm;PcmCalibration root;PcmFuelCalibration fuel;PcmIacCalibration iac;
    PcmAirCalibration air;PcmIoCalibration io;PcmMixtureCalibration mix;
    PcmFeedbackCalibration fb;PcmDeliveryCalibration dl;
    for(unsigned stop=1;stop<=4;++stop) {
        cycle_init(&f,&pcm,&root,&fuel,&iac,&air,&io,&mix,&fb,&dl,2);
        f.fail_at=stop;
        CHECK(pcm_fuel_cycle(&pcm)==PCM_NO_HARDWARE);
        CHECK(f.attempts==stop);
        CHECK(cycle_injector_writes(&f)==0);
        CHECK(pcm.system.fuel_ignition_counter==(stop>=4?8:7));
        CHECK(pcm.spark.density==0);
    }
}
static void cycle_running_uninhibited(void)
{
    static Fixture f;Pcm pcm;PcmCalibration root;PcmFuelCalibration fuel;PcmIacCalibration iac;
    PcmAirCalibration air;PcmIoCalibration io;PcmMixtureCalibration mix;
    PcmFeedbackCalibration fb;PcmDeliveryCalibration dl;
    cycle_init(&f,&pcm,&root,&fuel,&iac,&air,&io,&mix,&fb,&dl,2);
    root.mode_d=0; /* source authorization immediately granted */
    pcm.reference.latch_inhibited=false; /* source $0044.4 off */
    pcm.system.ignition_off=false; /* no once-only off-history clear */
    pcm.reference.additive_offset=0;
    pcm.iac.blm_value=128;
    pcm.fuel.integrator=128;
    pcm.spark.load_coordinate=50;
    pcm.spark.period_basis=0x1800;
    pcm.reference.rpm_coordinate=60;
    pcm.reference.delivered_pulse=0;
    CHECK(pcm_fuel_cycle(&pcm)==PCM_OK);
    CHECK(pcm.fuel.authorized);
    CHECK(pcm.system.fuel_ignition_counter==0);
    CHECK(f.memory[PCM_COPRST]==0x55);
    CHECK(pcm.spark.density==(uint16_t)((uint32_t)100u*65536u/694u+2649u));
    CHECK(cycle_injector_writes(&f)>=1);
}
int main(int argc,char **argv)
{
    if(argc==2 && strcmp(argv[1],"--contracts")!=0)return 2;
    cycle_authorization_zero_packet();
    cycle_running_uninhibited();
    cycle_trap_prevents_delivery();
    cycle_provider_failure_prefix();
    puts("Joined $7D4B..$8547 fuel path: all phases, zero-packet auth, trap and bus-failure histories pass.");
    return 0;
}
