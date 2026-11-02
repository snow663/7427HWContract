#include "control.h"
#include "reference_math.h"
/* D4DA..D4EA. High0284 remains the existing spark/IAC consumer owner. */
PcmStatus pcm_vss_filter(Pcm *pcm)
{
    if (pcm->calibration==NULL || pcm->calibration->io==NULL) return PCM_BAD_CONFIGURATION;
    uint16_t old=(uint16_t)((uint16_t)pcm->spark.vehicle_speed_high*256u+pcm->io.vehicle_speed_fraction);
    uint16_t filtered=pcm_lag16(pcm->io.vss_raw,old,pcm->calibration->io->vss_gain,NULL);
    pcm->spark.vehicle_speed_high=(uint8_t)(filtered>>8);pcm->io.vehicle_speed_fraction=(uint8_t)filtered;
    return PCM_OK;
}
