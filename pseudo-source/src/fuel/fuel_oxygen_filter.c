#include "fuel.h"
#include "mixture_internal.h"
#include "reference_math.h"
/* 7E09..7E35. Compare the lower threshold first, retaining inverted-window priority. */
PcmStatus pcm_fuel_oxygen_filter(Pcm *pcm)
{
    MIX_CAL();
    uint8_t gain = pcm->spark.idle_state ? cal->oxygen_idle_gain : pcm_lookup16(pcm->fuel.oxygen_coordinate, cal->oxygen_gain);
    uint8_t target = cal->oxygen_minimum;
    if (target <= pcm->fuel.raw_oxygen) target = cal->oxygen_maximum < pcm->fuel.raw_oxygen ? cal->oxygen_maximum : pcm->fuel.raw_oxygen;
    pcm->fuel.oxygen_filtered = pcm_lag8(target, pcm->fuel.oxygen_filtered, gain);
    return PCM_OK;
}
