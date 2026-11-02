#include "iac.h"
/* A2BA..A329. The RPM hold's expiry call skips divider decay; the other
 * dividers decay when already zero or when their decrement reaches zero. */
PcmStatus pcm_iac_slow_decays(Pcm *pcm)
{
    if (pcm->calibration == NULL || pcm->calibration->iac == NULL) return PCM_BAD_CONFIGURATION;
    const PcmIacCalibration *cal = pcm->calibration->iac;
    uint8_t amount = pcm->iac.switch_adder;
    if (amount != 0) {
        uint8_t delay = pcm->iac.switch_hold;
        if (delay != 0) pcm->iac.switch_hold = --delay;
        if (delay == 0) {
            amount = amount >= cal->switch_decay_amount ? (uint8_t)(amount - cal->switch_decay_amount) : 0;
            pcm->iac.switch_adder = amount;
            pcm->iac.switch_hold = amount == 0 ? 0 : cal->switch_decay_reload;
        }
    }
    amount = pcm->iac.startup_flow;
    if (amount != 0) {
        if (pcm->iac.startup_cancel) pcm->iac.startup_flow = 0;
        else {
            uint8_t divider = pcm->iac.startup_flow_divider;
            if (divider != 0) pcm->iac.startup_flow_divider = --divider;
            if (divider == 0) { pcm->iac.startup_flow_divider = cal->startup_flow_reload;pcm->iac.startup_flow = (uint8_t)(amount - 1u); }
        }
    }
    amount = pcm->iac.startup_rpm_adder;
    if (amount != 0) {
        if (pcm->iac.startup_cancel) pcm->iac.startup_rpm_adder = 0;
        else if (pcm->iac.startup_rpm_hold != 0) {
            if ((pcm->scheduler.phase & 0xf0u) == 0) --pcm->iac.startup_rpm_hold;
        } else {
            uint8_t divider = pcm->iac.startup_rpm_divider;
            if (divider != 0) pcm->iac.startup_rpm_divider = --divider;
            if (divider == 0) { pcm->iac.startup_rpm_divider = cal->startup_rpm_reload;pcm->iac.startup_rpm_adder = (uint8_t)(amount - 1u); }
        }
    }
    return PCM_OK;
}
