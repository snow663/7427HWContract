#include "iac.h"
/* A35C..A397: both baseline flags required, then a two-observation fault. */
PcmStatus pcm_iac_kicker_diagnostic(Pcm *pcm)
{
    if (pcm->calibration == NULL || pcm->calibration->iac == NULL) return PCM_BAD_CONFIGURATION;
    const PcmIacCalibration *cal = pcm->calibration->iac;
    if (!(cal->options & 4u) || !(cal->fault_options & 4u) || (pcm->iac.learning_flags & 4u) ||
        (pcm->iac.learning_flags & 3u) != 3u) return PCM_OK;
    uint8_t on = pcm->iac.baseline_on, off = pcm->iac.baseline_off;
    if (on < off || (uint8_t)(on - off) < cal->kicker_baseline_limit) {
        if (pcm->iac.state_flags & 0x40u) pcm->iac.kicker_fault = true;
        else pcm->iac.state_flags |= 0x40u;
    } else { pcm->iac.kicker_fault = false;pcm->iac.state_flags &= (uint8_t)~0x40u; }
    pcm->iac.learning_flags |= 4u;
    return PCM_OK;
}
