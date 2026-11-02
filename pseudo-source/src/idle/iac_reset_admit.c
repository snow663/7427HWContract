#include "iac.h"
/* A3E6..A3F9. Reuse the actual0044.4 owner; runtime.ignition_off is0051.3. */
PcmStatus pcm_iac_reset_admit(Pcm *pcm)
{
    if ((pcm->iac.state_flags & 1u) || (pcm->iac.state_flags & 4u)) return PCM_OK;
    if (pcm->reference.latch_inhibited) return pcm_iac_reset_request(pcm);
    if (pcm->calibration == NULL || pcm->calibration->iac == NULL) return PCM_BAD_CONFIGURATION;
    if (pcm->spark.vehicle_speed_high < pcm->calibration->iac->reset_speed) return PCM_OK;
    return pcm_iac_reset_request(pcm);
}
