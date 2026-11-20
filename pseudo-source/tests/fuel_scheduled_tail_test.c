#include "fuel.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define CHECK(x) do { if (!(x)) { fprintf(stderr,"Fuel tail %s:%d: %s\n",__FILE__,__LINE__,#x);exit(1); } } while(0)
typedef struct { PcmPlatform platform; PcmCalibration calibration; unsigned reads,governor_calls;uint8_t flags;bool fail; } Fixture;
static PcmStatus read8(void *ctx,uint16_t addr,uint8_t *sample)
{
    Fixture *f=ctx;CHECK(addr==0x006f);++f->reads;
    if(f->fail)return PCM_NO_HARDWARE;
    *sample=f->flags;return PCM_OK;
}
static PcmStatus governor(Pcm *pcm,PcmTask task)
{
    Fixture *f=pcm->platform->context;CHECK(task==PCM_GOVERNOR_TARGET);
    ++f->governor_calls;pcm->transmission.governor_requested_throttle=77;
    return PCM_OK;
}
static void init(Fixture *f,Pcm *pcm,uint8_t phase,uint8_t mode)
{
    memset(f,0,sizeof(*f));memset(pcm,0,sizeof(*pcm));
    f->platform.context=f;f->platform.read8=read8;
    f->calibration.mode_f=mode;
    pcm->platform=&f->platform;pcm->calibration=&f->calibration;
    pcm->scheduler.phase=phase;pcm->spark.battery_sample=50;
    pcm->transmission.governor_requested_throttle=12;
    pcm->unresolved_task=PCM_TASK_COUNT;
}
static void test_phase_two_defaults(void)
{
    static Fixture f;Pcm pcm;
    init(&f,&pcm,2,0);
    CHECK(pcm_fuel_scheduled_tail(&pcm)==PCM_OK);
    CHECK(pcm.transmission.governor_requested_throttle==255 && f.reads==0);
    init(&f,&pcm,2,1);pcm.runtime.spark_running=false;
    CHECK(pcm_fuel_scheduled_tail(&pcm)==PCM_OK);
    CHECK(pcm.transmission.governor_requested_throttle==255 && f.reads==0);
    init(&f,&pcm,2,1);pcm.runtime.spark_running=true;f.flags=0x34;
    CHECK(pcm_fuel_scheduled_tail(&pcm)==PCM_OK);
    CHECK(pcm.transmission.governor_requested_throttle==255 && f.reads==1);
    init(&f,&pcm,2,1);pcm.runtime.spark_running=true;f.flags=0;
    CHECK(pcm_fuel_scheduled_tail(&pcm)==PCM_UNIMPLEMENTED);
    CHECK(pcm.unresolved_task==PCM_GOVERNOR_TARGET);
    CHECK(pcm.transmission.governor_requested_throttle==12);
    CHECK(f.reads==1 && f.governor_calls==0);
}
static void test_enabled_and_failures(void)
{
    static Fixture f;Pcm pcm;
    init(&f,&pcm,2,1);pcm.runtime.spark_running=true;
    f.platform.task[PCM_GOVERNOR_TARGET]=governor;
    CHECK(pcm_fuel_scheduled_tail(&pcm)==PCM_OK);
    CHECK(f.reads==1 && f.governor_calls==1);
    CHECK(pcm.transmission.governor_requested_throttle==77);
    init(&f,&pcm,2,1);pcm.runtime.spark_running=true;f.fail=true;
    CHECK(pcm_fuel_scheduled_tail(&pcm)==PCM_NO_HARDWARE);
    CHECK(f.reads==1 && f.governor_calls==0);
    CHECK(pcm.transmission.governor_requested_throttle==12);
}
static void test_selected_elsewhere(void)
{
    static Fixture f;Pcm pcm;
    init(&f,&pcm,0,0);pcm.io.vss_age=8;
    CHECK(pcm_fuel_scheduled_tail(&pcm)==PCM_BAD_CONFIGURATION);
    CHECK(pcm.io.vss_age==8 && f.reads==0);
    init(&f,&pcm,4,0);pcm.io.vss_age=8;
    CHECK(pcm_fuel_scheduled_tail(&pcm)==PCM_BAD_CONFIGURATION);
    CHECK(pcm.io.vss_age==8 && f.reads==0);
    init(&f,&pcm,6,0);
    CHECK(pcm_fuel_scheduled_tail(&pcm)==PCM_BAD_CONFIGURATION);
    CHECK(f.reads==0);
    CHECK(pcm_fuel_scheduled_tail(NULL)==PCM_BAD_CONFIGURATION);
}
int main(int argc,char **argv)
{
    if(argc==2 && strcmp(argv[1],"--contracts")!=0)return 2;
    test_phase_two_defaults();test_enabled_and_failures();test_selected_elsewhere();
    puts("852C phase routing, governor defaults/dependency and no-I/O failure gates passed.");
    return 0;
}
