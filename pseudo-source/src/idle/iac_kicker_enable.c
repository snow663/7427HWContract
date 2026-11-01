#include "iac.h"
/* 9226..923F. The TPS-zero high-byte write deliberately retains02F7. */
PcmStatus pcm_iac_kicker_enable(Pcm *pcm)
{
    if (!(pcm->iac.kicker_flags & 4u)) {
        if (pcm->calibration == NULL || pcm->calibration->iac == NULL) return PCM_BAD_CONFIGURATION;
        const PcmIacCalibration *cal = pcm->calibration->iac;
        pcm->iac.tps_zero_high = (uint8_t)(pcm->iac.baseline_on + cal->kicker_tps_adder);
        pcm->iac.kicker_timer = cal->kicker_on_reload;
        pcm->iac.kicker_flags |= 4u;
    }
    pcm->iac.kicker_request = false;
    return PCM_OK;
}
