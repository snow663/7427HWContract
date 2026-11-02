#include "fuel.h"
/* Contiguous7EB2..7F85; VE/base fuel begins at7F86. */
PcmStatus pcm_fuel_acceleration(Pcm *pcm)
{
    PcmStatus result = pcm_fuel_map_acceleration(pcm);
    return result == PCM_OK ? pcm_fuel_tps_acceleration(pcm) : result;
}
