#include "fuel.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define CHECK(x) do {if(!(x)){fprintf(stderr,"Governor compute %s:%d: %s\n",__FILE__,__LINE__,#x);exit(1);}}while(0)

typedef struct {
    PcmPlatform platform;
    uint8_t data[0x70];
    unsigned attempts,fail_at,used;
    char kind[32];
    uint16_t addresses[32];
} Fixture;
static PcmStatus logop(Fixture *f,char kind,uint16_t address)
{
    if(++f->attempts==f->fail_at)return PCM_NO_HARDWARE;
    CHECK(f->used<32);
    f->kind[f->used]=kind;
    f->addresses[f->used++]=address;
    return PCM_OK;
}
static PcmStatus get8(void *context,uint16_t address,uint8_t *out)
{
    Fixture *f=context;CHECK(address>=0x50d8u && address<0x5148u);
    PcmStatus status=logop(f,'b',address);
    if(status==PCM_OK)*out=f->data[address-0x50d8u];
    return status;
}
static PcmStatus get16(void *context,uint16_t address,uint16_t *out)
{
    Fixture *f=context;CHECK(address>=0x50d8u && address+1u<0x5148u);
    PcmStatus status=logop(f,'w',address);
    if(status==PCM_OK)
        *out=(uint16_t)((uint16_t)f->data[address-0x50d8u]*256u+
                         f->data[address+1u-0x50d8u]);
    return status;
}
static void setup(Fixture *f,Pcm *pcm)
{
    memset(f,0,sizeof(*f));memset(pcm,0,sizeof(*pcm));
    f->platform.context=f;f->platform.read8=get8;f->platform.read16=get16;
    pcm->platform=&f->platform;
    f->data[0x50d9u-0x50d8u]=1;    /* signed target release threshold */
    f->data[0x50ddu-0x50d8u]=8;    /* secondary gain */
    f->data[0x50deu-0x50d8u]=9;    /* aux VSS gain */
    f->data[0x50dfu-0x50d8u]=16;   /* ordinary speed scalar */
    f->data[0x50e0u-0x50d8u]=64;   /* rpm scalar */
    f->data[0x50e1u-0x50d8u]=85;   /* TPS entry limit */
    f->data[0x50e2u-0x50d8u]=17;   /* minimum TPS */
    f->data[0x50e3u-0x50d8u]=12;   /* lead minimum TPS */
    f->data[0x50e5u-0x50d8u]=50;   /* lead mode threshold */
    f->data[0x50e6u-0x50d8u]=4;    /* lead rate high gain */
    f->data[0x50e7u-0x50d8u]=9;    /* lead rate low gain */
    f->data[0x50e8u-0x50d8u]=32;   /* F499 clamp */
    for(unsigned n=0;n<5;++n)f->data[0x50e9u-0x50d8u+n]=(uint8_t)(2u*n+2u);
    f->data[0x50eeu-0x50d8u]=16;   /* F4B6 scale for lead curve */
    f->data[0x50efu-0x50d8u]=12;f->data[0x50f0u-0x50d8u]=32;
    f->data[0x50f1u-0x50d8u]=64;f->data[0x50f2u-0x50d8u]=96;
    for(unsigned n=0;n<17;++n)f->data[0x50fau-0x50d8u+n]=(uint8_t)(5u+n);
    pcm->transmission.governor_requested_throttle=64;
    pcm->transmission.governor_vehicle_error=7;
    pcm->transmission.governor_speed_error=9;
    pcm->transmission.governor_tps_baseline=0x6400;
    pcm->transmission.governor_integrator=0x1000;
    pcm->reference.throttle=31;
    pcm->reference.coolant=64;
    pcm->spark.rpm_monitor_delta=0;
    pcm->spark.rpm_monitor_filtered=0;
}
static void test_rate(void)
{
    static Fixture f;Pcm pcm;
    setup(&f,&pcm);
    CHECK(pcm_fuel_governor_rate(&pcm)==PCM_OK);
    /* capped curve 50E8=32 -> knot #2 has gain 6 */
    CHECK(pcm.transmission.governor_primary_step==21u);
    CHECK(pcm.transmission.governor_secondary_step==288u);
    CHECK(pcm.transmission.governor_auxiliary_adjust==0u);
    CHECK(f.used==5);
    CHECK(f.kind[0]=='b' && f.addresses[0]==0x50e8u);
    CHECK(f.kind[1]=='w' && f.addresses[1]==0x50ebu);
    CHECK(f.kind[2]=='b' && f.addresses[2]==0x50ebu);
    CHECK(f.addresses[3]==0x50dfu && f.addresses[4]==0x50ddu);
    setup(&f,&pcm);pcm.transmission.governor_flags=0x80u;
    CHECK(pcm_fuel_governor_rate(&pcm)==PCM_OK);
    CHECK(pcm.transmission.governor_primary_step==21u);
    CHECK(pcm.transmission.governor_secondary_step==1008u);
    CHECK(pcm.transmission.governor_auxiliary_adjust==3u);
    setup(&f,&pcm);pcm.transmission.governor_flags=0x81u;
    CHECK(pcm_fuel_governor_rate(&pcm)==PCM_OK);
    CHECK(pcm.transmission.governor_primary_step==108u);
    CHECK(pcm.transmission.governor_secondary_step==1008u);
    setup(&f,&pcm);pcm.transmission.governor_requested_throttle=255;
    CHECK(pcm_fuel_governor_rate(&pcm)==PCM_OK);
    CHECK(f.used==6 && f.addresses[0]==0x50e8u && f.addresses[1]==0x50e8u);
    /* The first step stores before a failed gain read. */
    setup(&f,&pcm);f.fail_at=4;
    CHECK(pcm_fuel_governor_rate(&pcm)==PCM_NO_HARDWARE);
    CHECK(pcm.transmission.governor_primary_step==336u);
    CHECK(pcm.transmission.governor_secondary_step==0);
    setup(&f,&pcm);f.fail_at=5;
    CHECK(pcm_fuel_governor_rate(&pcm)==PCM_NO_HARDWARE);
    CHECK(pcm.transmission.governor_primary_step==21u);
    CHECK(pcm.transmission.governor_secondary_step==0);
}
static void test_ordinary(void)
{
    static Fixture f;Pcm pcm;uint8_t candidate;
    setup(&f,&pcm);
    CHECK(pcm_fuel_governor_compute(&pcm,true)==PCM_OK);
    CHECK(pcm.transmission.governor_tps_baseline==0x6415u);
    CHECK(pcm.transmission.governor_requested_throttle==101u);
    setup(&f,&pcm);pcm.transmission.governor_flags=0x44u;
    CHECK(pcm_fuel_governor_compute(&pcm,true)==PCM_OK);
    CHECK(pcm.transmission.governor_tps_baseline==0x63ebu);
    CHECK(pcm.transmission.governor_requested_throttle==98u);
    setup(&f,&pcm);pcm.transmission.governor_flags=0x80u;
    CHECK(pcm_fuel_governor_compute(&pcm,true)==PCM_OK);
    CHECK(pcm.transmission.governor_tps_baseline==0x6415u);
    CHECK(pcm.transmission.governor_requested_throttle==107u);
    setup(&f,&pcm);pcm.transmission.governor_flags=0x81u;
    pcm.transmission.governor_integrator=0;
    CHECK(pcm_fuel_governor_compute(&pcm,true)==PCM_OK);
    CHECK(pcm.transmission.governor_tps_baseline==0x646cu);
    CHECK(pcm.transmission.governor_requested_throttle==107u);
    CHECK((pcm.transmission.governor_flags&0x13u)==0);
    setup(&f,&pcm);pcm.transmission.governor_flags=0x44u;
    pcm.transmission.governor_tps_baseline=1u;
    CHECK(pcm_fuel_governor_compute(&pcm,true)==PCM_OK);
    CHECK(pcm.transmission.governor_tps_baseline==0x1100u);
    CHECK(pcm.transmission.governor_requested_throttle==17u);
    setup(&f,&pcm);
    pcm.transmission.governor_tps_baseline=0x6415u;
    pcm.transmission.governor_primary_step=0;pcm.transmission.governor_secondary_step=0;
    candidate=0;
    CHECK(pcm_fuel_governor_ordinary(&pcm,&candidate)==PCM_OK);
    CHECK(candidate==100u);
    CHECK(pcm_fuel_governor_ordinary(&pcm,NULL)==PCM_BAD_CONFIGURATION);
}
static void test_lead(void)
{
    static Fixture f;Pcm pcm;uint8_t candidate;
    setup(&f,&pcm);
    CHECK(pcm_fuel_governor_compute(&pcm,false)==PCM_OK);
    CHECK(pcm.transmission.governor_tps_baseline==0xff00u);
    CHECK(pcm.transmission.governor_requested_throttle==255u);
    setup(&f,&pcm);pcm.transmission.governor_flags=0x02u;
    pcm.transmission.governor_speed_error=4u;
    CHECK(pcm_fuel_governor_compute(&pcm,false)==PCM_OK);
    CHECK((pcm.transmission.governor_flags&0x10u)!=0);
    CHECK(pcm.transmission.governor_tps_baseline==0x6410u);
    CHECK(pcm.transmission.governor_requested_throttle==100u);
    setup(&f,&pcm);pcm.transmission.governor_flags=0x02u;
    pcm.spark.rpm_monitor_delta=16u;
    pcm.transmission.governor_speed_error=4u;
    CHECK(pcm_fuel_governor_compute(&pcm,false)==PCM_OK);
    CHECK(pcm.transmission.governor_tps_baseline<=0x6400u);
    CHECK(pcm.transmission.governor_auxiliary_adjust==0);
    setup(&f,&pcm);pcm.spark.rpm_monitor_delta=0x80u;
    CHECK(pcm_fuel_governor_compute(&pcm,false)==PCM_OK);
    CHECK(pcm.transmission.governor_tps_baseline==0xff00u);
    CHECK(pcm_fuel_governor_lead(&pcm,NULL)==PCM_BAD_CONFIGURATION);
}
static void test_finish(void)
{
    static Fixture f;Pcm pcm;
    setup(&f,&pcm);
    pcm.transmission.governor_flags=0x40u;
    pcm.transmission.governor_auxiliary_adjust=50u;
    CHECK(pcm_fuel_governor_finish(&pcm,60u)==PCM_OK);
    CHECK(pcm.transmission.governor_requested_throttle==60u); /* 40 not 84 */
    setup(&f,&pcm);
    pcm.transmission.governor_flags=0xc0u;
    pcm.transmission.governor_auxiliary_adjust=50u;
    CHECK(pcm_fuel_governor_finish(&pcm,60u)==PCM_OK);
    CHECK(pcm.transmission.governor_requested_throttle==17u);
    setup(&f,&pcm);
    pcm.transmission.governor_flags=0x84u;
    pcm.transmission.governor_auxiliary_adjust=50u;
    CHECK(pcm_fuel_governor_finish(&pcm,220u)==PCM_OK);
    CHECK(pcm.transmission.governor_requested_throttle==255u);
    setup(&f,&pcm);
    pcm.transmission.governor_flags=0x81u;
    pcm.transmission.governor_integrator=0;
    CHECK(pcm_fuel_governor_finish(&pcm,80u)==PCM_OK);
    CHECK(pcm.transmission.governor_requested_throttle==80u);
    CHECK((pcm.transmission.governor_flags&0x13u)==0);
    setup(&f,&pcm);pcm.transmission.governor_flags=0xc0u;
    pcm.transmission.governor_auxiliary_adjust=50u;f.fail_at=1;
    CHECK(pcm_fuel_governor_finish(&pcm,60u)==PCM_NO_HARDWARE);
    CHECK(pcm.transmission.governor_requested_throttle==64u);
    CHECK(pcm.transmission.governor_flags==0xc0u);
}
int main(int argc,char **argv)
{
    if(argc==2 && strcmp(argv[1],"--contracts")!=0)return 2;
    test_rate();test_ordinary();test_lead();test_finish();
    CHECK(pcm_fuel_governor_compute(NULL,false)==PCM_BAD_CONFIGURATION);
    puts("$8F5F..$90D2 governor rates, ordinary/lead selection, retained baseline and final command contracts pass.");
    return 0;
}
