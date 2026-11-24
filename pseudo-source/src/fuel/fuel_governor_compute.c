#include "fuel.h"
#define GOV_RUN(call) do {PcmStatus status=(call);if(status!=PCM_OK)return status;}while(0)

/* BMHM $8F5F..$90D2. Source selection originates from $8F56 after
 * the $8F3B..$8F5C mode update. Both alternatives enter the identical
 * $9097 output/cleanup tail with A holding the candidate TPS high byte. */
PcmStatus pcm_fuel_governor_compute(Pcm *pcm,bool ordinary)
{
    if(pcm==NULL)return PCM_BAD_CONFIGURATION;
    uint8_t candidate=0;
    if(ordinary) {
        GOV_RUN(pcm_fuel_governor_rate(pcm));
        GOV_RUN(pcm_fuel_governor_ordinary(pcm,&candidate));
    } else {
        GOV_RUN(pcm_fuel_governor_lead(pcm,&candidate));
    }
    return pcm_fuel_governor_finish(pcm,candidate);
}
