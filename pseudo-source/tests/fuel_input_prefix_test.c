#include "fuel.h"
#include "hardware.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define CHECK(x) do { if (!(x)) { fprintf(stderr,"Fuel prefix %s:%d: %s\n",__FILE__,__LINE__,#x);exit(1); } } while (0)
typedef struct {
    uint8_t memory[65536];
    unsigned used,governor_calls;
    bool governor_fail;
    uint8_t governor_throttle;
    uint16_t governor_oxygen,governor_previous_density;
    PcmPlatform platform;
    PcmCalibration root;
    PcmIoCalibration io;
    PcmAirCalibration air;
    PcmMixtureCalibration mixture;
} Fixture;
static PcmStatus read8(void *v,uint16_t a,uint8_t *out)
{
    Fixture *f=v;++f->used;*out=f->memory[a];return PCM_OK;
}
static PcmStatus read16(void *v,uint16_t a,uint16_t *out)
{
    Fixture *f=v;++f->used;
    *out=(uint16_t)((uint16_t)f->memory[a]*256u+f->memory[(uint16_t)(a+1u)]);
    return PCM_OK;
}
static PcmStatus write8(void *v,uint16_t a,uint8_t value)
{
    Fixture *f=v;++f->used;f->memory[a]=value;return PCM_OK;
}
static PcmStatus write16(void *v,uint16_t a,uint16_t value)
{
    Fixture *f=v;++f->used;f->memory[a]=(uint8_t)(value>>8);
    f->memory[(uint16_t)(a+1u)]=(uint8_t)value;return PCM_OK;
}
static PcmStatus mask_irq(void *v,bool masked)
{
    Fixture *f=v;(void)masked;++f->used;return PCM_OK;
}
static PcmStatus governor(Pcm *pcm,PcmTask task)
{
    Fixture *f=pcm->platform->context;
    CHECK(task==PCM_FUEL_GOVERNOR);
    ++f->governor_calls;
    f->governor_throttle=pcm->reference.throttle;
    f->governor_oxygen=pcm->fuel.oxygen_filtered;
    f->governor_previous_density=pcm->spark.density;
    if(f->governor_fail)return PCM_NO_HARDWARE;
    pcm->spark.map_filtered=(uint8_t)(pcm->spark.map_filtered+3u);
    return PCM_OK;
}
static void init(Fixture *f,Pcm *pcm,bool option,bool bound)
{
    memset(f,0,sizeof(*f));memset(pcm,0,sizeof(*pcm));
    f->root.mode_f=(uint8_t)(0x80u+(option?1u:0u));
    f->root.io=&f->io;f->root.air=&f->air;f->root.mixture=&f->mixture;
    f->io.map_rpm_delta_limit=4;f->io.map_hold_reload=9;
    f->air.throttle_gain=64;f->air.throttle_default=33;
    f->mixture.oxygen_minimum=25;f->mixture.oxygen_maximum=220;
    f->mixture.oxygen_idle_gain=128;
    f->platform.context=f;
    f->platform.read8=read8;f->platform.read16=read16;
    f->platform.write8=write8;f->platform.write16=write16;
    f->platform.mask_irq=mask_irq;
    if(bound)f->platform.task[PCM_FUEL_GOVERNOR]=governor;
    pcm->platform=&f->platform;pcm->calibration=&f->root;
    pcm->unresolved_task=PCM_TASK_COUNT;
    pcm->io.map_previous_rpm=49;pcm->io.map_hold=2;pcm->io.coolant_context=0xa0;
    pcm->spark.rpm_high=50;pcm->spark.idle_state=true;
    pcm->spark.map_filtered=100;pcm->spark.density=0x1111;
    pcm->fuel.raw_throttle=120;pcm->fuel.raw_oxygen=128;
    pcm->iac.tps_zero_high=40;
    pcm->reference.throttle=11;
    f->memory[0x0044]=0x10;f->memory[0x027f]=7;
    f->memory[0x400a]=16;
}
static void test_no_governor(void)
{
    static Fixture f;Pcm pcm;init(&f,&pcm,false,false);
    CHECK(pcm_fuel_input_prefix(&pcm)==PCM_OK);
    CHECK(f.used==4 && f.memory[0x027f]==8 && f.memory[PCM_COPRST]==0x55);
    CHECK(pcm.io.map_hold==1 && pcm.io.map_transient);
    CHECK(pcm.spark.previous_throttle==11 && pcm.reference.throttle==80);
    CHECK(pcm.fuel.oxygen_filtered!=0);
    CHECK(pcm.spark.density==(uint16_t)(100u*65536u/694u+2649u));
    CHECK(f.governor_calls==0 && pcm.unresolved_task==PCM_TASK_COUNT);
}
static void test_governor_boundary(void)
{
    static Fixture f;Pcm pcm;init(&f,&pcm,true,false);
    CHECK(pcm_fuel_input_prefix(&pcm)==PCM_UNIMPLEMENTED);
    CHECK(pcm.unresolved_task==PCM_FUEL_GOVERNOR);
    CHECK(pcm.io.map_hold==1 && pcm.reference.throttle==80);
    CHECK(pcm.fuel.oxygen_filtered!=0);
    CHECK(pcm.spark.density==0x1111);
    CHECK(f.memory[PCM_COPRST]==0x55);
}
static void test_governor_success_failure(void)
{
    static Fixture f;Pcm pcm;init(&f,&pcm,true,true);
    CHECK(pcm_fuel_input_prefix(&pcm)==PCM_OK);
    CHECK(f.governor_calls==1 && f.governor_throttle==80);
    CHECK(f.governor_oxygen!=0 && f.governor_previous_density==0x1111);
    CHECK(pcm.spark.map_filtered==103 && pcm.spark.density==(uint16_t)(103u*65536u/694u+2649u));
    init(&f,&pcm,true,true);f.governor_fail=true;
    CHECK(pcm_fuel_input_prefix(&pcm)==PCM_NO_HARDWARE);
    CHECK(f.governor_calls==1 && pcm.spark.density==0x1111);
}
static void test_early_stop(void)
{
    static Fixture f;Pcm pcm;init(&f,&pcm,false,false);
    f.memory[0x027f]=16;
    CHECK(pcm_fuel_input_prefix(&pcm)==PCM_HALT_BOUNDARY);
    CHECK(pcm.reference.throttle==11 && pcm.spark.density==0x1111);
    CHECK(pcm.io.map_hold==2 && pcm.fuel.oxygen_filtered==0);
    init(&f,&pcm,false,false);pcm.calibration=NULL;
    CHECK(pcm_fuel_input_precalculate(&pcm)==PCM_BAD_CONFIGURATION);
    CHECK(pcm_fuel_input_precalculate(NULL)==PCM_BAD_CONFIGURATION);
    init(&f,&pcm,false,false);f.memory[0x027f]=16;
    CHECK(pcm_fuel_cycle(&pcm)==PCM_HALT_BOUNDARY);
    CHECK(pcm.spark.density==0x1111 && pcm.reference.throttle==11);
    init(&f,&pcm,true,false);
    CHECK(pcm_fuel_cycle(&pcm)==PCM_UNIMPLEMENTED);
    CHECK(pcm.unresolved_task==PCM_FUEL_GOVERNOR && pcm.spark.density==0x1111);
}
int main(int argc,char **argv)
{
    if(argc==2 && strcmp(argv[1],"--contracts")!=0)return 2;
    test_no_governor();test_governor_boundary();
    test_governor_success_failure();test_early_stop();
    puts("Joined MAP/TPS/O2/density, optional governor and early-stop contracts pass.");
    return 0;
}
