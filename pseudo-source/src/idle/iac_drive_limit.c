#include "iac.h"
/* A32A..A35B: cap only a drive cell with both qualification bits clear. */
PcmStatus pcm_iac_drive_limit(Pcm *pcm)
{
    if (!(pcm->iac.context & 2u) || (pcm->iac.context & 0x0cu)) return PCM_OK;
    if (pcm->calibration == NULL || pcm->calibration->iac == NULL) return PCM_BAD_CONFIGURATION;
    const PcmIacCalibration *cal = pcm->calibration->iac;
    unsigned ac = pcm->iac.context & 1u;
    uint16_t limit = (uint16_t)(ac ? pcm->iac.bank[1].ac_snapshot : pcm->iac.bank[1].no_ac_snapshot) + cal->drive_snapshot_delta[ac];
    if (limit > 255u) return PCM_OK;
    if (ac) { if ((pcm->iac.bank[1].ac >> 8) > limit) pcm->iac.bank[1].ac = (uint16_t)(limit << 8); }
    else if ((pcm->iac.bank[1].no_ac >> 8) > limit) pcm->iac.bank[1].no_ac = (uint16_t)(limit << 8);
    return PCM_OK;
}
