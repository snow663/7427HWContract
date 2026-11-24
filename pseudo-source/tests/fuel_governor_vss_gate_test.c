#include "fuel.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define CHECK(x) do {if(!(x)){fprintf(stderr,"Governor VSS %s:%d: %s\n",__FILE__,__LINE__,#x);exit(1);}}while(0)
typedef struct {PcmPlatform platform;unsigned attempts,fail_at,used;uint16_t addresses[4];uint8_t threshold,hysteresis,throttle_limit;} Fixture;
static PcmStatus read8(void *ctx,uint16_t address,uint8_t *value)
{
    Fixture *f=ctx;CHECK(address==0x50dau||address==0x50dbu||address==0x50e1u);
    if(++f->attempts==f->fail_at)return PCM_NO_HARDWARE;
    CHECK(f->used<4);f->addresses[f->used++]=address;
    *value=address==0x50dau?f->threshold:
           address==0x50dbu?f->hysteresis:f->throttle_limit;
    return PCM_OK;
}
static void init(Fixture *f,Pcm *p,unsigned threshold,unsigned speed,unsigned frac,
                 unsigned flags,unsigned tps)
{
    memset(f,0,sizeof(*f));memset(p,0,sizeof(*p));
    f->platform.context=f;f->platform.read8=read8;p->platform=&f->platform;
    f->threshold=(uint8_t)threshold;f->hysteresis=42;f->throttle_limit=85;
    p->spark.vehicle_speed_high=(uint8_t)speed;
    p->io.vehicle_speed_fraction=(uint8_t)frac;
    p->reference.throttle=(uint8_t)tps;
    p->transmission.governor_flags=(uint8_t)flags;
    p->transmission.governor_vehicle_error=0x7a;
    p->transmission.governor_tps_baseline=0x1234;
}
static void oracle(const Fixture *f,const Pcm *p,uint8_t *flags,uint8_t *error,
                   uint16_t *baseline,unsigned *reads)
{
    *flags=p->transmission.governor_flags;
    *error=p->transmission.governor_vehicle_error;
    *baseline=p->transmission.governor_tps_baseline;
    *reads=1;
    if(f->threshold==0u){*flags&=(uint8_t)~0x80u;return;}
    uint8_t speed=p->spark.vehicle_speed_high,frac=p->io.vehicle_speed_fraction;
    uint16_t delta;
    if(speed>=f->threshold){
        delta=(uint16_t)((((uint16_t)(speed-f->threshold))<<8)|frac);
        uint32_t scaled=4u*(uint32_t)delta;
        *error=(uint8_t)((scaled>65535u?65535u:scaled)>>8);
        *flags|=0x40u;
        if(!(*flags&0x80u)){
            uint8_t initial=f->throttle_limit<p->reference.throttle?
                f->throttle_limit:p->reference.throttle;
            *baseline=(uint16_t)((uint16_t)initial<<8|(*baseline&255u));
            *flags|=0x80u;
            *reads=2;
        }
        *flags&=(uint8_t)~0x13u;
        return;
    }
    delta=(uint16_t)((((uint16_t)(f->threshold-speed))<<8)-frac);
    uint32_t scaled=4u*(uint32_t)delta;
    *error=(uint8_t)((scaled>65535u?65535u:scaled)>>8);
    *flags&=(uint8_t)~0x40u;
    if(!(*flags&0x80u)){*flags&=(uint8_t)~0x80u;return;}
    *reads=2;
    if(*error>=f->hysteresis)*flags&=(uint8_t)~0x80u;
    else *flags&=(uint8_t)~0x13u;
}
static void test_range(void)
{
    static Fixture f;Pcm p;
    const uint8_t fractions[]={0,1,127,255};
    const uint8_t flags[]={0,0x80,0xc0,0xff};
    unsigned count=0;
    for(unsigned threshold=0;threshold<256;++threshold)
      for(unsigned speed=0;speed<256;++speed)
       for(unsigned variant=0;variant<4;++variant){
        init(&f,&p,threshold,speed,fractions[variant],flags[variant],200);
        uint8_t expect_flags,expect_error;uint16_t expect_baseline;unsigned reads;
        oracle(&f,&p,&expect_flags,&expect_error,&expect_baseline,&reads);
        CHECK(pcm_fuel_governor_vss_gate(&p)==PCM_OK);
        CHECK(p.transmission.governor_flags==expect_flags);
        CHECK(p.transmission.governor_vehicle_error==expect_error);
        CHECK(p.transmission.governor_tps_baseline==expect_baseline);
        CHECK(f.used==reads);
        CHECK(f.addresses[0]==0x50dau);
        if(reads==2)CHECK(f.addresses[1]==(speed>=threshold?0x50e1u:0x50dbu));
        ++count;
       }
    CHECK(count==262144u);
    puts("262144 source VSS/threshold/fraction/flag combinations pass.");
}
static void test_failures(void)
{
    static Fixture f;Pcm p;
    init(&f,&p,30,50,255,0,200);
    f.fail_at=1;
    CHECK(pcm_fuel_governor_vss_gate(&p)==PCM_NO_HARDWARE);
    CHECK(f.used==0 && p.transmission.governor_flags==0);
    init(&f,&p,30,50,255,0,200);
    f.fail_at=2;
    CHECK(pcm_fuel_governor_vss_gate(&p)==PCM_NO_HARDWARE);
    CHECK(f.used==1 && f.addresses[0]==0x50dau);
    CHECK((p.transmission.governor_flags&0x40u)!=0);
    CHECK(p.transmission.governor_tps_baseline==0x1234);
    init(&f,&p,30,20,1,0x80,200);
    f.fail_at=2;
    CHECK(pcm_fuel_governor_vss_gate(&p)==PCM_NO_HARDWARE);
    CHECK(f.used==1 && f.addresses[0]==0x50dau);
    CHECK((p.transmission.governor_flags&0x40u)==0);
    CHECK(p.transmission.governor_tps_baseline==0x1234);
    CHECK(pcm_fuel_governor_vss_gate(NULL)==PCM_BAD_CONFIGURATION);
}
int main(int argc,char **argv)
{
    if(argc==2 && strcmp(argv[1],"--contracts")!=0)return 2;
    test_range();test_failures();
    return 0;
}
