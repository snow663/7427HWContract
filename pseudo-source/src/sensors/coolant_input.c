#include "board_io.h"
/* C96A..C9BF. Range bit004E.0 shares the existing board output owner. */
PcmStatus pcm_coolant_input(Pcm *pcm)
{
    if (pcm->calibration == NULL || pcm->calibration->air == NULL) return PCM_BAD_CONFIGURATION;
    const PcmAirCalibration *cal = pcm->calibration->air;
    bool first = pcm->runtime.first_conversion || (pcm->io.auxiliary_output & 1u);
    uint8_t value = cal->coolant_table[first ? 0 : 1][pcm->io.raw_coolant];
    pcm->io.coolant_conversion = value;
    if (value > 120u) pcm->io.auxiliary_output &= (uint8_t)~1u;
    else if (value <= 106u) pcm->io.auxiliary_output |= 1u;
    if (pcm->runtime.primary_faults & 0x60u)
        value = pcm->scheduler.run_counter > cal->coolant_runtime_limit ? cal->coolant_default_late : cal->coolant_default_early;
    pcm->reference.coolant = value;
    pcm->runtime.first_conversion = false;
    value = pcm->reference.coolant < 16u ? 0 : (uint8_t)(pcm->reference.coolant - 16u);
    pcm->iac.coolant_index = value > 192u ? 192u : value;
    return PCM_OK;
}
