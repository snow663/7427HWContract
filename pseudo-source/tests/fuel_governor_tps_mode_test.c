#include "fuel.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define CHECK(x) do {if(!(x)){fprintf(stderr,"Gov TPS mode %s:%d: %s\n",__FILE__,__LINE__,#x);exit(1);}}while(0)
int main(int argc,char **argv)
{
    if(argc==2 && strcmp(argv[1],"--contracts")!=0)return 2;
    Pcm pcm;bool ordinary=false;unsigned count=0;
    CHECK(pcm_fuel_governor_tps_mode(NULL,&ordinary)==PCM_BAD_CONFIGURATION);
    CHECK(pcm_fuel_governor_tps_mode(&pcm,NULL)==PCM_BAD_CONFIGURATION);
    for(unsigned flags=0;flags<256u;++flags)for(unsigned tps=0;tps<256u;++tps) {
        memset(&pcm,0,sizeof(pcm));
        pcm.reference.throttle=(uint8_t)tps;
        pcm.transmission.governor_flags=(uint8_t)flags;
        pcm.transmission.governor_tps_baseline=0x7fa5;
        ordinary=false;
        uint8_t new_flags=(uint8_t)flags;
        uint16_t baseline=0x7fa5;
        if(flags&4u) {
            if(!(flags&0x81u) && tps<=127u)
                baseline=(uint16_t)(((uint16_t)tps<<8)|0xa5u);
            new_flags=(uint8_t)((new_flags|1u)&~0x12u);
        }
        CHECK(pcm_fuel_governor_tps_mode(&pcm,&ordinary)==PCM_OK);
        CHECK(pcm.transmission.governor_flags==new_flags);
        CHECK(pcm.transmission.governor_tps_baseline==baseline);
        CHECK(ordinary==((new_flags&0x81u)!=0));
        ++count;
    }
    CHECK(count==65536u);
    puts("65536 source-aligned $8F3B governor TPS/flag/mode combinations pass.");
    return 0;
}
