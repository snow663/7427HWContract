/* Machine-readable C fixture for the independent BMHM governor ROM replay.
 * The 64 KB input is a verified *recorded evidence view*, not a flash image.
 * This fixture never accesses physical hardware. */
#include "fuel.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define CHECK(x) do {if(!(x)){fprintf(stderr,"governor ROM fixture: %s:%d: %s\n",__FILE__,__LINE__,#x);return 3;}}while(0)

typedef struct {
    PcmPlatform platform;
    uint8_t image[65536];
    unsigned fail_at,attempts;
} Fixture;
static PcmStatus read8(void *ctx,uint16_t address,uint8_t *out)
{
    Fixture *f=ctx;
    if(++f->attempts==f->fail_at)return PCM_NO_HARDWARE;
    *out=f->image[address];return PCM_OK;
}
static PcmStatus read16(void *ctx,uint16_t address,uint16_t *out)
{
    Fixture *f=ctx;
    if(++f->attempts==f->fail_at)return PCM_NO_HARDWARE;
    *out=(uint16_t)(((uint16_t)f->image[address]<<8)|
            f->image[(uint16_t)(address+1u)]);
    return PCM_OK;
}
static PcmStatus write16(void *ctx,uint16_t address,uint16_t value)
{
    Fixture *f=ctx;
    if(++f->attempts==f->fail_at)return PCM_NO_HARDWARE;
    f->image[address]=(uint8_t)(value>>8);
    f->image[(uint16_t)(address+1u)]=(uint8_t)value;return PCM_OK;
}
static uint16_t word(const Fixture *f,uint16_t address)
{
    return (uint16_t)(((uint16_t)f->image[address]<<8)|
                        f->image[(uint16_t)(address+1u)]);
}
static void store_word(Fixture *f,uint16_t address,uint16_t value)
{
    f->image[address]=(uint8_t)(value>>8);
    f->image[(uint16_t)(address+1u)]=(uint8_t)value;
}
static void load(Pcm *pcm,Fixture *f,PcmCalibration *cal)
{
    memset(pcm,0,sizeof(*pcm));memset(cal,0,sizeof(*cal));
    f->attempts=0;
    f->platform.context=f;
    f->platform.read8=read8;f->platform.read16=read16;
    f->platform.write16=write16;pcm->platform=&f->platform;
    pcm->unresolved_task=PCM_TASK_COUNT;pcm->calibration=cal;
    cal->mode_f=f->image[0x400f];
    pcm->scheduler.profiling_enabled=(f->image[0x86]&0x40u)!=0;
    pcm->runtime.spark_running=(f->image[0x4f]&0x80u)!=0;
    pcm->reference.throttle=f->image[0x1d9];
    pcm->reference.coolant=f->image[0x06];
    pcm->spark.rpm_monitor_delta=f->image[0x28d];
    pcm->spark.rpm_monitor_filtered=word(f,0x28e);
    pcm->spark.vehicle_speed_high=f->image[0x284];
    pcm->io.vehicle_speed_fraction=f->image[0x285];
    pcm->transmission.governor_flags=f->image[0x75];
    pcm->transmission.governor_speed_error=f->image[0x293];
    pcm->transmission.governor_vehicle_error=f->image[0x294];
    pcm->transmission.governor_requested_throttle=f->image[0x299];
    pcm->transmission.governor_throttle_error=f->image[0x29a];
    pcm->transmission.governor_tps_baseline=word(f,0x286);
    pcm->transmission.governor_integrator=word(f,0x288);
    pcm->transmission.governor_primary_step=word(f,0x28a);
    pcm->transmission.governor_secondary_step=word(f,0x290);
    pcm->transmission.governor_auxiliary_adjust=f->image[0x292];
    pcm->transmission.governor_proportional=word(f,0x295);
    pcm->transmission.governor_integral_gain=word(f,0x297);
}
static void save(Fixture *f,const Pcm *pcm)
{
    f->image[0x75]=pcm->transmission.governor_flags;
    f->image[0x293]=pcm->transmission.governor_speed_error;
    f->image[0x294]=pcm->transmission.governor_vehicle_error;
    f->image[0x299]=pcm->transmission.governor_requested_throttle;
    f->image[0x29a]=pcm->transmission.governor_throttle_error;
    store_word(f,0x286,pcm->transmission.governor_tps_baseline);
    store_word(f,0x288,pcm->transmission.governor_integrator);
    store_word(f,0x28a,pcm->transmission.governor_primary_step);
    store_word(f,0x290,pcm->transmission.governor_secondary_step);
    f->image[0x292]=pcm->transmission.governor_auxiliary_adjust;
    store_word(f,0x295,pcm->transmission.governor_proportional);
    store_word(f,0x297,pcm->transmission.governor_integral_gain);
}
static const uint16_t output_addresses[]={
    0x75,0x4f,0x86,0x006f,0x1d9,0x284,0x285,0x286,0x287,0x288,0x289,
    0x28a,0x28b,0x28d,0x28e,0x28f,0x290,0x291,0x292,0x293,0x294,
    0x295,0x296,0x297,0x298,0x299,0x29a,0x306c,0x306d,
};
static int evaluate(Fixture *f,unsigned mode)
{
    Pcm pcm;PcmCalibration calibration;uint8_t candidate=0;
    load(&pcm,f,&calibration);
    PcmStatus status=PCM_BAD_CONFIGURATION;
    switch(mode) {
    case 0:status=pcm_fuel_governor_target(&pcm);break;
    case 1:status=pcm_fuel_governor_compute(&pcm,true);break;
    case 2:status=pcm_fuel_governor_compute(&pcm,false);break;
    case 3:status=pcm_fuel_governor_drive(&pcm);break;
    case 4:status=pcm_fuel_governor_rate(&pcm);break;
    case 5:status=pcm_fuel_governor_ordinary(&pcm,&candidate);break;
    case 6:status=pcm_fuel_governor_lead(&pcm,&candidate);break;
    case 7:status=pcm_fuel_governor_finish(&pcm,f->image[0x901]);break;
    default:return 2;
    }
    save(f,&pcm);
    printf("{\"status\":%u,\"value\":%u,\"state\":[",(unsigned)status,(unsigned)candidate);
    for(unsigned i=0;i<sizeof(output_addresses)/sizeof(output_addresses[0]);++i)
        printf("%s%u",i?",":"",(unsigned)f->image[output_addresses[i]]);
    puts("]}");
    return 0;
}
int main(int argc,char **argv)
{
    if(argc!=2)return 2;
    FILE *file=fopen(argv[1],"rb");
    if(file==NULL)return 2;
    static uint8_t image[65536];
    int good=fread(image,1,sizeof(image),file)==sizeof(image);
    fclose(file);if(!good)return 2;
    static Fixture f;
    unsigned mode,count;
    while(scanf("%u %u",&mode,&count)==2) {
        CHECK(count<2048);
        memcpy(f.image,image,sizeof(f.image));
        for(unsigned i=0;i<count;++i) {
            unsigned address,value;CHECK(scanf("%u %u",&address,&value)==2);
            CHECK(address<=65535u && value<=255u);
            f.image[address]=(uint8_t)value;
        }
        f.fail_at=0;
        if(evaluate(&f,mode)!=0)return 2;
    }
    return ferror(stdin)?2:0;
}
