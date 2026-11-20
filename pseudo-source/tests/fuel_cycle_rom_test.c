/* Independent full-entry $7D4B ROM comparison: typed C fixture.
 * Uses the established delivery fixture for all calibration/backing tables.
 * Input ROM file is SHA-checked by the Python caller, NEVER flash output. */
#define PCM_DELIVERY_TEST_MAIN inherited_full_entry_main
#include "fuel_delivery_test.c"
#undef PCM_DELIVERY_TEST_MAIN

static uint16_t be(const uint8_t *memory,uint16_t a)
{
    return (uint16_t)((uint16_t)memory[a]<<8|memory[(uint16_t)(a+1u)]);
}
static void setup_full(Fixture *f,Pcm *pcm,PcmCalibration *root,
    PcmFuelCalibration *fuel,PcmIacCalibration *iac,PcmAirCalibration *air,
    PcmIoCalibration *io,PcmMixtureCalibration *mix,PcmFeedbackCalibration *fb,
    PcmDeliveryCalibration *dl,const uint8_t *image)
{
    delivery_init(f,pcm,root,fuel,iac,air,io,mix,fb,dl);
    memcpy(f->memory+0x4000,image+0x4000,0xc000); /* full hash-identified stock */
    f->platform.bind_fuel_ram_owners=true;
    pcm->unresolved_task=PCM_TASK_COUNT;
}
static void load_full(Pcm *pcm,Fixture *f,PcmCalibration *root)
{
    delivery_transfer(pcm,f,true);
    pcm->system.fuel_ignition_counter=be(f->memory,0x027e);
    pcm->runtime.ignition_off=(f->memory[0x51]&8u)!=0;
    pcm->runtime.spark_running=(f->memory[0x4f]&0x80u)!=0;
    pcm->spark.bypass_supervision=(f->memory[4]&0x80u)!=0;
    pcm->spark.run_transition=(f->memory[4]&8u)!=0;
    pcm->runtime.refresh_late=(f->memory[4]&4u)!=0;
    pcm->fuel.oxygen_warmed=(f->memory[4]&2u)!=0;
    pcm->fuel.oxygen_activity=(f->memory[4]&1u)!=0;
    pcm->reference.bank_fault=(f->memory[0x19]&0x40u)!=0;
    pcm->spark.est_fault=(f->memory[0x19]&0x20u)!=0;
    pcm->reference.enrichment_age=f->memory[0x268];
    pcm->system.retained_initialized=(f->memory[0x86]&8u)!=0;
    pcm->scheduler.profiling_enabled=(f->memory[0x86]&0x40u)!=0;
    pcm->spark.first_reference=(f->memory[0x44]&8u)!=0;
    pcm->runtime.output_override=(f->memory[0x44]&4u)!=0;
    pcm->io.egr_failure_count=f->memory[0x223];
    pcm->fuel.startup_park_hold=f->memory[0x27d];
    pcm->spark.idle_state=(f->memory[0x50]&0x80u)!=0;
    pcm->io.map_previous_rpm=f->memory[0x65];
    pcm->io.map_context=(uint8_t)(f->memory[0x47]&0xfeu);
    pcm->io.map_transient=(f->memory[0x47]&1u)!=0;
    pcm->io.map_hold=f->memory[0x1c5];
    pcm->io.coolant_context=f->memory[0x3e];
    pcm->fuel.oxygen_filtered=be(f->memory,0x1d2);
    pcm->fuel.oxygen_coordinate=f->memory[0x27b];
    pcm->transmission.range_context=f->memory[0x89];
    pcm->spark.rpm_monitor_delta=f->memory[0x28d];
    pcm->spark.rpm_monitor_filtered=be(f->memory,0x28e);
    pcm->transmission.governor_flags=f->memory[0x75];
    pcm->transmission.governor_requested_throttle=f->memory[0x299];
    pcm->transmission.governor_tps_baseline=be(f->memory,0x286);
    pcm->transmission.governor_integrator=be(f->memory,0x288);
    pcm->transmission.governor_vehicle_error=f->memory[0x294];
    pcm->transmission.governor_speed_error=f->memory[0x293];
    pcm->io.vehicle_speed_fraction=f->memory[0x285];
    root->mode_f=f->memory[0x400f];
    root->mode_d=f->memory[0x400d];
}
static uint16_t W(const Pcm *p,uint16_t a,const Fixture *f)
{
    switch(a) {
    case 0x027e:return p->system.fuel_ignition_counter;
    case 0x01d2:return p->fuel.oxygen_filtered;
    case 0x0257:return p->spark.density;
    case 0x024c:return p->reference.delivered_pulse;
    case 0x01de:return p->fuel.throttle_decel_filter;
    case 0x01dc:return p->fuel.tps_history;
    case 0x023a:return p->fuel.acceleration_reservoir;
    default:return be(f->memory,a);
    }
}
static uint8_t B(const Pcm *p,uint16_t a,const Fixture *f)
{
    uint16_t value;
    if(a==0x0257||a==0x0258) {
        value=p->spark.density;
        return a==0x0257?(uint8_t)(value>>8):(uint8_t)value;
    }
    if(a==0x027e||a==0x027f||a==0x01d2||a==0x01d3||
       a==0x024c||a==0x024d||a==0x01de||a==0x01df||
       a==0x01dc||a==0x01dd||a==0x023a||a==0x023b) {
        value=W(p,(uint16_t)(a&0xfffeu),f);
        return (a&1u)?(uint8_t)value:(uint8_t)(value>>8);
    }
    switch(a) {
    case 0x01c5:return p->io.map_hold;
    case 0x01d9:return p->reference.throttle;
    case 0x0062:return p->reference.rpm_coordinate;
    case 0x0299:return p->transmission.governor_requested_throttle;
    case 0x024a:return p->fuel.commanded_afr;
    case 0x0231:return p->fuel.volumetric_efficiency;
    case 0x020f:return p->fuel.integrator;
    case 0x01d5:return p->fuel.raw_oxygen;
    default:return f->memory[a];
    }
}
static const uint16_t check_addresses[]={
    0x027e,0x027f,0x0044,0x004f,0x0051,0x0062,0x01c5,
    0x01d9,0x01d2,0x01d3,0x0257,0x0258,0x024c,0x024d,
    0x303a,0x3fce,0x3fcf,0x0299,0x01de,0x01df,0x01dc,0x01dd,
};
int main(int argc,char **argv)
{
    if(argc!=2)return 2;
    FILE *in=fopen(argv[1],"rb");if(!in)return 2;
    static uint8_t image[65536];
    int correct=fread(image,1,sizeof(image),in)==sizeof(image);
    fclose(in);if(!correct)return 2;
    static Fixture f;Pcm pcm;PcmCalibration root;PcmFuelCalibration fuel;PcmIacCalibration iac;
    PcmAirCalibration air;PcmIoCalibration io;PcmMixtureCalibration mix;
    PcmFeedbackCalibration fb;PcmDeliveryCalibration dl;
    unsigned count;
    while(scanf("%u",&count)==1) {
        if(count>=1024)return 3;
        setup_full(&f,&pcm,&root,&fuel,&iac,&air,&io,&mix,&fb,&dl,image);
        for(unsigned i=0;i<count;++i) {
            unsigned addr,val;
            if(scanf("%u %u",&addr,&val)!=2||addr>=65536||val>=256)return 3;
            f.memory[addr]=(uint8_t)val;
        }
        load_full(&pcm,&f,&root);
        PcmStatus status=pcm_fuel_cycle(&pcm);
        printf("{\"status\":%u,\"state\":[",(unsigned)status);
        for(unsigned i=0;i<sizeof(check_addresses)/sizeof(check_addresses[0]);++i)
            printf("%s%u",i?",":"",(unsigned)B(&pcm,check_addresses[i],&f));
        puts("]}");
    }
    return 0;
}
