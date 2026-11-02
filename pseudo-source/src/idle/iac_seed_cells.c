#include "iac.h"
/* 92A4..92F0. Only the high bytes of the four integral words are seeded. */
PcmStatus pcm_iac_seed_cells(Pcm *pcm)
{
    if (pcm->calibration == NULL || pcm->calibration->iac == NULL) return PCM_BAD_CONFIGURATION;
    const PcmIacCalibration *cal = pcm->calibration->iac;
    uint8_t addition = pcm->reference.coolant < cal->default_coolant ? cal->default_ac_cold : cal->default_ac_warm;
    for (unsigned order = 0; order < 2; ++order) {
        unsigned i = 1u - order;
        uint8_t base = cal->default_integral[i];
        uint16_t ac = (uint16_t)base + addition;
        if (ac > 255u) ac = 255;
        pcm->iac.bank[i].no_ac = (uint16_t)(((uint16_t)base << 8) | (pcm->iac.bank[i].no_ac & 255u));
        pcm->iac.bank[i].no_ac_snapshot = base;
        pcm->iac.bank[i].ac = (uint16_t)((ac << 8) | (pcm->iac.bank[i].ac & 255u));
        pcm->iac.bank[i].ac_snapshot = (uint8_t)ac;
    }
    pcm->iac.baseline_on = cal->default_baseline;
    return PCM_OK;
}
