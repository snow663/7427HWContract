#include "iac.h"
#include "reference_math.h"
/* 9411..9536, including the direct park or common flow-conversion tail. */
PcmStatus pcm_iac_start(Pcm *pcm)
{
    if (pcm->calibration == NULL || pcm->calibration->iac == NULL) return PCM_BAD_CONFIGURATION;
    const PcmIacCalibration *cal = pcm->calibration->iac;
    uint8_t coolant = pcm->iac.coolant_index;
    for (unsigned i = 0; i < 2; ++i) pcm->iac.hold[i] = pcm_lookup16(coolant, cal->start_hold_curve[i]);
    pcm->iac.startup_flow = cal->start_flow;
    pcm->iac.startup_flow_divider = cal->startup_flow_reload;
    uint8_t coordinate = coolant > 160u ? (uint8_t)(2u * (coolant - 160u) + 160u) : coolant;
    unsigned drive = cal->options & 1u;
    uint8_t base = pcm_lookup16(coordinate, cal->rpm_curve[drive ? 2 : 0]);
    uint8_t addition = pcm_lookup16(coordinate, cal->start_rpm_curve);
    pcm->iac.startup_rpm_adder = addition;
    if (!drive) {
        uint32_t product = 2u * (uint32_t)addition * cal->startup_rpm_gain;
        addition = product > 65535u ? 255u : (uint8_t)(product >> 8);
    }
    pcm->spark.iac_desired_speed = (uint8_t)(base + addition);
    pcm->iac.startup_rpm_divider = cal->startup_rpm_reload;
    pcm->iac.startup_rpm_hold = cal->start_rpm_hold;
    pcm->iac.proportional = pcm->iac.gear_adder = pcm->iac.gear_hold = 0;
    pcm->iac.ac_adder = pcm->iac.ac_hold = pcm->iac.dfco_adder = 0;
    pcm->iac.switch_adder = pcm->iac.qualification_delay = 0;
    pcm->iac.derivative_filtered = (uint16_t)(0x8000u | (pcm->iac.derivative_filtered & 255u));
    pcm->iac.context &= (uint8_t)~0xbdu;
    pcm->spark.override_request = false; /* 0036.5 shares the cleared mask. */
    pcm->iac.kicker_flags &= (uint8_t)~0x9bu;
    pcm->iac.transfer_flags &= (uint8_t)~0x7fu;
    pcm->iac.learning_flags &= (uint8_t)~0xc7u;
    pcm->iac.rpm_error_filtered = (uint16_t)(((uint16_t)cal->warm_error_limit << 8) | (pcm->iac.rpm_error_filtered & 255u));
    pcm->iac.state_flags &= (uint8_t)~2u;
    for (unsigned order = 0; order < 2; ++order) {
        unsigned i = 1u - order;
        uint16_t cold = (uint16_t)((uint16_t)pcm_lookup16(coolant, cal->start_cold_curve[i]) << 8);
        pcm->iac.bank[i].cold = cold;pcm->iac.bank[i].bound = cold;
    }
    pcm->iac.cold_delay = pcm_lookup16(coolant, cal->cold_delay_curve);
    pcm->iac.selected_integral = (cal->options & 0x20u) ? (uint16_t)((uint16_t)cal->default_integral[drive] << 8) : pcm->iac.bank[drive].no_ac;
    pcm->iac.selected_cold = pcm->iac.bank[drive].cold;
    pcm->iac.composite_flow = UINT16_MAX;
    if (pcm->reference.coolant < cal->prestart_coolant_minimum) {
        pcm->iac.target = cal->park_target;return PCM_OK;
    }
    uint32_t flow = (uint32_t)pcm->iac.selected_integral + ((uint16_t)pcm->iac.startup_flow << 8);
    if (flow <= 65535u) flow += pcm->iac.selected_cold;
    return pcm_iac_convert(pcm, flow > 65535u ? UINT16_MAX : (uint16_t)flow);
}
