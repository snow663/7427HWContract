#include "fuel.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define CHECK(x) do {if(!(x)){fprintf(stderr,"Fuel tail %s:%d: %s\n",__FILE__,__LINE__,#x);exit(1);}}while(0)

typedef struct {
    PcmPlatform platform;PcmCalibration calibration;
    unsigned status_reads,cal_reads,cal_word_reads;
    uint8_t option_status;
    bool fail_status,fail_cal;
    uint8_t cal[0x40];
} Fixture;
static PcmStatus read8(void *ctx,uint16_t addr,uint8_t *sample)
{
    Fixture *f=ctx;
    if(addr==0x006fu) {
        ++f->status_reads;
        if(f->fail_status)return PCM_NO_HARDWARE;
        *sample=f->option_status;return PCM_OK;
    }
    CHECK(addr>=0x50d8u && addr<0x5118u);
    ++f->cal_reads;
    if(f->fail_cal)return PCM_NO_HARDWARE;
    *sample=f->cal[addr-0x50d8u];
    return PCM_OK;
}
static PcmStatus read16(void *ctx,uint16_t addr,uint16_t *sample)
{
    Fixture *f=ctx;
    CHECK(addr>=0x50d8u && addr<0x5117u);
    ++f->cal_word_reads;
    if(f->fail_cal)return PCM_NO_HARDWARE;
    *sample=(uint16_t)((uint16_t)f->cal[addr-0x50d8u]*256u+
                         f->cal[addr-0x50d8u+1u]);
    return PCM_OK;
}
static void init(Fixture *f,Pcm *pcm,uint8_t phase,uint8_t mode)
{
    memset(f,0,sizeof(*f));memset(pcm,0,sizeof(*pcm));
    f->platform.context=f;f->platform.read8=read8;f->platform.read16=read16;
    f->calibration.mode_f=mode;f->cal[0]=20; /* 50D8 RPM target */
    f->cal[0x0a]=0; /* 50E2 minimum TPS */
    f->cal[0x16]=0; /* 50EE scaled lead-RPM table header */
    pcm->platform=&f->platform;pcm->calibration=&f->calibration;
    pcm->scheduler.phase=phase;pcm->spark.battery_sample=50;
    pcm->transmission.governor_requested_throttle=12;
    pcm->unresolved_task=PCM_TASK_COUNT;
}
static void test_disabled_or_unqualified(void)
{
    static Fixture f;Pcm pcm;
    init(&f,&pcm,2,0);
    CHECK(pcm_fuel_scheduled_tail(&pcm)==PCM_OK);
    CHECK(pcm.transmission.governor_requested_throttle==255 && f.status_reads==0);
    init(&f,&pcm,2,1);
    CHECK(pcm_fuel_scheduled_tail(&pcm)==PCM_OK);
    CHECK(pcm.transmission.governor_requested_throttle==255 && f.status_reads==0);
    init(&f,&pcm,2,1);pcm.runtime.spark_running=true;f.option_status=0x34;
    CHECK(pcm_fuel_scheduled_tail(&pcm)==PCM_OK);
    CHECK(pcm.transmission.governor_requested_throttle==255 && f.status_reads==1);
}
static void test_resident_governor(void)
{
    static Fixture f;Pcm pcm;
    init(&f,&pcm,2,1);pcm.runtime.spark_running=true;
    CHECK(pcm_fuel_scheduled_tail(&pcm)==PCM_OK);
    CHECK(f.status_reads==1 && f.cal_reads>=3 && f.cal_word_reads==1);
    CHECK(pcm.transmission.governor_speed_error==20);
    CHECK(pcm.transmission.governor_requested_throttle==255);
    CHECK(pcm.transmission.governor_tps_baseline==0xff00);
    CHECK(pcm.unresolved_task==PCM_TASK_COUNT);
}
static void test_failure_prefixes(void)
{
    static Fixture f;Pcm pcm;
    init(&f,&pcm,2,1);pcm.runtime.spark_running=true;f.fail_status=true;
    CHECK(pcm_fuel_scheduled_tail(&pcm)==PCM_NO_HARDWARE);
    CHECK(f.status_reads==1 && f.cal_reads==0);
    CHECK(pcm.transmission.governor_requested_throttle==12);
    init(&f,&pcm,2,1);pcm.runtime.spark_running=true;f.fail_cal=true;
    pcm.transmission.governor_flags=0xffu;
    CHECK(pcm_fuel_scheduled_tail(&pcm)==PCM_NO_HARDWARE);
    CHECK(f.status_reads==1 && f.cal_reads==1 && f.cal_word_reads==0);
    CHECK(pcm.transmission.governor_flags==0xfbu);
}
static void test_other_phases(void)
{
    static Fixture f;Pcm pcm;
    init(&f,&pcm,0,0);pcm.io.vss_age=8;
    CHECK(pcm_fuel_scheduled_tail(&pcm)==PCM_BAD_CONFIGURATION);
    CHECK(pcm.io.vss_age==8 && f.status_reads==0);
    init(&f,&pcm,4,0);pcm.io.vss_age=8;
    CHECK(pcm_fuel_scheduled_tail(&pcm)==PCM_BAD_CONFIGURATION);
    CHECK(pcm.io.vss_age==8 && f.status_reads==0);
    init(&f,&pcm,6,0);
    CHECK(pcm_fuel_scheduled_tail(&pcm)==PCM_BAD_CONFIGURATION);
    CHECK(f.status_reads==0);
    CHECK(pcm_fuel_scheduled_tail(NULL)==PCM_BAD_CONFIGURATION);
}
static PcmStatus headsup(Pcm *pcm,PcmTask task)
{
    CHECK(task==PCM_GOVERNOR_HEADSUP);
    pcm->transmission.governor_headsup_carry=true;
    pcm->transmission.governor_headsup_result=0x42;
    return PCM_OK;
}
static void test_headsup_carry(void)
{
    static Fixture f;Pcm pcm;
    init(&f,&pcm,2,1);pcm.runtime.spark_running=true;
    pcm.scheduler.profiling_enabled=true;
    CHECK(pcm_fuel_scheduled_tail(&pcm)==PCM_UNIMPLEMENTED);
    CHECK(pcm.unresolved_task==PCM_GOVERNOR_HEADSUP);
    CHECK(f.status_reads==1 && f.cal_reads==1 && f.cal_word_reads==0);
    init(&f,&pcm,2,1);pcm.runtime.spark_running=true;
    pcm.scheduler.profiling_enabled=true;
    f.platform.task[PCM_GOVERNOR_HEADSUP]=headsup;
    CHECK(pcm_fuel_scheduled_tail(&pcm)==PCM_OK);
    CHECK(pcm.transmission.governor_requested_throttle==0x42);
    CHECK(f.cal_reads==1 && f.cal_word_reads==0);
}
int main(int argc,char **argv)
{
    if(argc==2 && strcmp(argv[1],"--contracts")!=0)return 2;
    test_disabled_or_unqualified();test_resident_governor();
    test_failure_prefixes();test_other_phases();test_headsup_carry();
    puts("852C phase routing, complete governor target and 1809 carry boundaries pass.");
    return 0;
}
