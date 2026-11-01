#include "iac.h"
#include "reference_math.h"
static uint8_t rounded(uint8_t a, uint8_t b)
{ return (uint8_t)(((uint16_t)a * b + 128u) >> 8); }
/* 9FDE..A12C. Bound-high admission, delayed cold decay and queued opposite-bank
 * transfer; the disjoint warm route writes snapshots rather than cell words. */
PcmStatus pcm_iac_cold(Pcm *pcm)
{
    if (pcm->calibration == NULL || pcm->calibration->iac == NULL) return PCM_BAD_CONFIGURATION;
    const PcmIacCalibration *cal = pcm->calibration->iac;
    if ((pcm->iac.bank[0].bound >> 8) || (pcm->iac.bank[1].bound >> 8)) {
        uint8_t delay = pcm->iac.cold_delay;
        if (delay != 0) pcm->iac.cold_delay = (uint8_t)(delay - 1u);
        else {
            for (unsigned bank = 0; bank < 2; ++bank) {
                uint16_t bound = pcm_gain_word(pcm->iac.bank[bank].bound, cal->cold_decay_gain);
                if ((bound >> 8) == 0) bound = 0;
                pcm->iac.bank[bank].bound = bound;
                uint16_t cold = bound == 0 ? 0 : pcm_gain_word(pcm->iac.bank[bank].cold, cal->cold_gain[bank]);
                if (cold > pcm->iac.bank[bank].bound) cold = pcm->iac.bank[bank].bound;
                pcm->iac.bank[bank].cold = cold;
            }
            uint8_t reload = 0;
            if ((pcm->iac.bank[0].bound >> 8) || (pcm->iac.bank[1].bound >> 8)) {
                uint8_t a = pcm_lookup16(pcm->iac.coolant_index, cal->cold_delay_curve);
                uint8_t t = pcm->iac.runtime_high;
                if (t > 64u) t = 64u;
                uint32_t product = 2u * (uint32_t)a * pcm_lookup16(t, cal->cold_runtime_curve);
                reload = product > 65535u ? 255u : (uint8_t)(product >> 8);
            }
            pcm->iac.cold_delay = reload;
        }
        unsigned bank = (pcm->iac.context & 2u) != 0;
        uint8_t current = (uint8_t)(pcm->iac.bank[bank].cold >> 8);
        if (current == 0) return PCM_OK;
        uint8_t gain = cal->cold_upper[bank];
        if (gain != 0) {
            uint16_t upper = (uint16_t)current + rounded(current, gain);
            if (upper <= 255u && upper < (pcm->iac.bank[bank ^ 1u].cold >> 8)) {
                pcm->iac.cold_proposed[bank ^ 1u] = (uint16_t)(upper << 8);
                pcm->iac.transfer_flags |= 0x10u;
                return PCM_OK;
            }
        }
        current = (uint8_t)(pcm->iac.bank[bank].cold >> 8);
        gain = cal->cold_lower[bank];
        if (gain != 0) {
            uint8_t lower = (uint8_t)(current - rounded(current, gain));
            if (lower < (pcm->iac.bank[bank ^ 1u].cold >> 8)) pcm->iac.transfer_flags &= (uint8_t)~0x10u;
            else {
                pcm->iac.cold_proposed[bank ^ 1u] = (uint16_t)((uint16_t)lower << 8);
                pcm->iac.transfer_flags |= 0x10u;
            }
        }
    } else if ((pcm->iac.context & 0x0cu) == 0x0cu && pcm->reference.coolant >= cal->warm_coolant_minimum &&
               pcm->reference.coolant <= cal->warm_coolant_maximum && pcm->iac.rpm_error <= cal->warm_error_limit &&
               (pcm->iac.rpm_error_filtered >> 8) <= cal->warm_error_limit) {
        pcm->iac.learning_fault = false;
        unsigned bank = (pcm->iac.context & 2u) != 0;
        if (pcm->iac.context & 1u) {
            pcm->iac.bank[bank].ac_snapshot = (uint8_t)(pcm->iac.bank[bank].ac >> 8);
            if (bank) pcm->iac.state_flags |= 0x20u;
        } else {
            pcm->iac.bank[bank].no_ac_snapshot = (uint8_t)(pcm->iac.bank[bank].no_ac >> 8);
            if (bank) pcm->iac.state_flags |= 0x10u;
        }
    }
    return PCM_OK;
}
