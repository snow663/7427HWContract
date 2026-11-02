#include "fuel.h"
/* Contiguous7F86..8031; broader fuel admission, AE and corrections are separate. */
PcmStatus pcm_fuel_air_charge(Pcm *pcm)
{
    PcmStatus result = pcm_fuel_ve(pcm);
    return result == PCM_OK ? pcm_fuel_base_publish(pcm) : result;
}
