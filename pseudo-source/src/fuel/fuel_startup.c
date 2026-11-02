#include "fuel.h"
/* E33C..E476. E477 onward remains outside this slice. */
PcmStatus pcm_fuel_startup(Pcm *pcm)
{
    if (!pcm->runtime.fuel_running) return pcm_fuel_startup_seed(pcm);
    PcmStatus result = pcm_fuel_startup_context(pcm);
    if (result != PCM_OK) return result;
    result = pcm_fuel_startup_afr(pcm);
    return result == PCM_OK ? pcm_fuel_startup_spark(pcm) : result;
}
