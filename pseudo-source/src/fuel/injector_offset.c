#include "fuel.h"
#include "reference_math.h"
/* E2FB..E305 slice, before the slot-F phase gate and its remaining work. */
PcmStatus pcm_injector_offset(Pcm *pcm)
{
    if (pcm->calibration == NULL || pcm->calibration->fuel == NULL) return PCM_BAD_CONFIGURATION;
    pcm->reference.additive_offset = pcm_lookup16(pcm->spark.battery_sample, pcm->calibration->fuel->offset);
    return PCM_OK;
}
