#include "fuel.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define CHECK(x) do {if(!(x)){fprintf(stderr,"Governor error %s:%d: %s\n",__FILE__,__LINE__,#x);exit(1);}}while(0)
typedef struct { PcmPlatform platform;unsigned reads;uint8_t cal;bool fail; } Fixture;
static PcmStatus read8(void *ctx,uint16_t address,uint8_t *sample)
{
    Fixture *f=ctx;CHECK(address==0x50d8u);++f->reads;
    if(f->fail)return PCM_NO_HARDWARE;
    *sample=f->cal;return PCM_OK;
}
static void init(Fixture *f,Pcm *pcm,uint8_t limit,uint8_t high)
{
    memset(f,0,sizeof(*f));memset(pcm,0,sizeof(*pcm));
    f->platform.context=f;f->platform.read8=read8;f->cal=limit;
    pcm->platform=&f->platform;pcm->spark.rpm_monitor_filtered=(uint16_t)((uint16_t)high<<8);
    pcm->transmission.governor_flags=0xff;
    pcm->transmission.governor_speed_error=0x5a;
}
int main(int argc,char **argv)
{
    if(argc==2 && strcmp(argv[1],"--contracts")!=0)return 2;
    static Fixture f;Pcm pcm;
    CHECK(pcm_fuel_governor_error(NULL)==PCM_BAD_CONFIGURATION);
    for(unsigned target=0;target<256u;++target)for(unsigned actual=0;actual<256u;++actual) {
        init(&f,&pcm,(uint8_t)target,(uint8_t)actual);
        CHECK(pcm_fuel_governor_error(&pcm)==PCM_OK);
        CHECK(f.reads==1);
        CHECK(pcm.transmission.governor_speed_error==(uint8_t)
            (target>=actual?target-actual:actual-target));
        CHECK((pcm.transmission.governor_flags&0x04u)==(target<actual?4u:0u));
        CHECK((pcm.transmission.governor_flags&0xfbu)==0xfbu);
    }
    init(&f,&pcm,3,100);f.fail=true;
    CHECK(pcm_fuel_governor_error(&pcm)==PCM_NO_HARDWARE);
    CHECK(f.reads==1 && pcm.transmission.governor_flags==0xfb);
    CHECK(pcm.transmission.governor_speed_error==0x5a);
    puts("65536 source-backed $8EC9 unsigned-error and direction cases pass.");
    return 0;
}
