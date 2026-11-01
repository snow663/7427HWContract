#include "iac.h"
/* A39C..A3E5. The caller owns the earlier phase-bit5 return. Old count>limit
 * sets the fault; an old count equal toFF wraps without setting it. */
PcmStatus pcm_iac_learning_diagnostic(Pcm *pcm)
{
    if (pcm->calibration == NULL || pcm->calibration->iac == NULL) return PCM_BAD_CONFIGURATION;
    const PcmIacCalibration *cal = pcm->calibration->iac;
    if (!(cal->fault_options & 8u)) return PCM_OK;
    if ((pcm->runtime.primary_faults & 0x10u) || (pcm->runtime.primary_faults & 1u) || pcm->iac.input_fault ||
        pcm->iac.low_battery || !(pcm->iac.context & 8u) || (pcm->iac.state_flags & 0x40u) ||
        pcm->iac.bank[1].cold != 0 || pcm->iac.bank[0].cold != 0 ||
        (pcm->iac.rpm_error_filtered >> 8) <= cal->learning_error_limit) {
        pcm->iac.learning_count = 0;pcm->iac.learning_fault = false;
    } else {
        uint8_t count = pcm->iac.learning_count;
        if (count > cal->learning_count_limit) pcm->iac.learning_fault = true;
        else pcm->iac.learning_count = (uint8_t)(count + 1u);
    }
    return PCM_OK;
}
