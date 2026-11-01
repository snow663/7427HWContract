#include "iac.h"
/* A12D..A153: an expiring AC divider decays on this call; a hold retains it. */
PcmStatus pcm_iac_transition_decay(Pcm *pcm)
{
    if (pcm->calibration == NULL || pcm->calibration->iac == NULL) return PCM_BAD_CONFIGURATION;
    const PcmIacCalibration *cal = pcm->calibration->iac;
    uint8_t amount = pcm->iac.ac_adder;
    if (amount != 0 && pcm->iac.ac_hold == 0) {
        if (!(pcm->iac.context & 1u)) pcm->iac.ac_adder = 0;
        else {
            uint8_t divider = pcm->iac.ac_divider;
            if (divider != 0) pcm->iac.ac_divider = --divider;
            if (divider == 0) {
                pcm->iac.ac_divider = cal->ac_decay_reload;
                pcm->iac.ac_adder = amount >= cal->ac_decay_amount ? (uint8_t)(amount - cal->ac_decay_amount) : 0;
            }
        }
    }
    return PCM_OK;
}
