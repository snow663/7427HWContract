#include "iac.h"
#include "reference_math.h"
/* 9537..969D: retain the old context across both transition producers. */
PcmStatus pcm_iac_context(Pcm *pcm)
{
    if (pcm->calibration == NULL || pcm->calibration->iac == NULL) return PCM_BAD_CONFIGURATION;
    const PcmIacCalibration *cal = pcm->calibration->iac;
    uint8_t old = pcm->iac.context;
    bool drive = (pcm->calibration->mode_f & 0x40u) ? !pcm->iac.park_neutral : !(pcm->iac.gear_status & 0x50u);
    if (drive) pcm->iac.context |= 2u;else pcm->iac.context &= (uint8_t)~2u;
    if (drive != ((old & 2u) != 0)) {
        unsigned i = drive ? 1 : 0;
        uint8_t hold = cal->gear_hold[i], delay = cal->gear_delay[i];
        if (pcm->reference.coolant < cal->gear_coolant) {
            hold = (uint8_t)(hold + cal->gear_cold_hold[i]);
            delay = (uint8_t)(delay + cal->gear_cold_delay[i]);
        }
        pcm->iac.gear_hold = hold;pcm->iac.gear_adder = cal->gear_flow[i];
        delay = (uint8_t)(delay + hold);
        if (delay > pcm->iac.qualification_delay) pcm->iac.qualification_delay = delay;
    }
    PcmIacBank *bank = &pcm->iac.bank[drive ? 1 : 0];
    uint8_t difference = (uint8_t)((bank->ac >> 8) - (bank->no_ac >> 8));
    bool ac = pcm->iac.ac_request;
    if (ac) pcm->iac.context |= 1u;else pcm->iac.context &= (uint8_t)~1u;
    if (ac != ((old & 1u) != 0) && (ac || pcm->iac.ac_hold == 0)) {
        unsigned i = ac ? 1 : 0;uint8_t amount;
        if (ac) pcm->iac.ac_divider = cal->ac_decay_reload;
        if (ac && (cal->options & 0x40u)) {
            PcmStatus result = pcm_lookup_offset(pcm->spark.mat_sample, &cal->ac_temperature, &amount);
            if (result != PCM_OK) return result;
        } else {
            amount = (uint8_t)(((uint16_t)difference * cal->ac_transition_gain[i]) >> 8);
            if (amount < cal->ac_transition_minimum[i]) amount = cal->ac_transition_minimum[i];
            if (amount > cal->ac_transition_maximum[i]) amount = cal->ac_transition_maximum[i];
        }
        pcm->iac.ac_adder = amount;pcm->iac.ac_hold = cal->ac_transition_hold[i];
        uint8_t delay = (uint8_t)(cal->ac_transition_delay[i] + cal->ac_transition_hold[i]);
        if (delay > pcm->iac.qualification_delay) pcm->iac.qualification_delay = delay;
    }
    if ((old ^ pcm->iac.context) & 3u) {
        unsigned g = drive ? 1 : 0, a = ac ? 1 : 0, bit = 1u << (2u * g + a);
        if (pcm->iac.transfer_flags & bit) {
            if (ac) bank->ac = pcm->iac.proposed[g][1];else bank->no_ac = pcm->iac.proposed[g][0];
        }
        if (pcm->iac.transfer_flags & 0x10u) {
            if (((pcm->iac.bank[0].bound | pcm->iac.bank[1].bound) >> 8) == 0) pcm->iac.transfer_flags &= (uint8_t)~0x10u;
            else if ((old ^ pcm->iac.context) & 2u) {
                bank->cold = pcm->iac.cold_proposed[g];pcm->iac.transfer_flags &= (uint8_t)~0x10u;
            }
        }
        pcm->iac.transfer_flags &= (uint8_t)~0x0fu;
    }
    return PCM_OK;
}
