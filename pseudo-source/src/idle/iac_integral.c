#include "iac.h"
#include "iac_math.h"
#include "reference_math.h"
/* 99C5..9C1F: local words model the six-byte frame, never old X/Y RAM. */
PcmStatus pcm_iac_integral(Pcm *pcm)
{
    if (pcm->calibration == NULL || pcm->calibration->iac == NULL) return PCM_BAD_CONFIGURATION;
    const PcmIacCalibration *cal = pcm->calibration->iac;
    unsigned gear = (pcm->iac.context & 2u) != 0, ac = pcm->iac.context & 1u;
    PcmIacBank *bank = &pcm->iac.bank[gear];
    uint16_t integral = ac ? bank->ac : bank->no_ac, cold = bank->cold;
    bool high = (pcm->iac.context & 0x80u) != 0, admitted = false, commit = false;
    if (pcm->reference.throttle >= cal->closed_throttle) pcm->iac.learning_flags |= 0x80u;
    else pcm->iac.learning_flags &= (uint8_t)~0x80u;
    if ((pcm->iac.learning_flags & 0x80u) || pcm->spark.vehicle_speed_high >= cal->closed_speed) {
        pcm->iac.qualification_delay = cal->closed_delay;
        pcm->iac.context &= (uint8_t)~4u;
    } else {
        pcm->iac.context |= 4u;
        if ((pcm->iac.follower_filtered >> 8) <= pcm->iac.follower_closed_threshold) {
            if (pcm->iac.qualification_delay != 0) --pcm->iac.qualification_delay;
            else {
                admitted = pcm->iac.hold[high ? 1 : 0] == 0;
                goto qualification;
            }
        }
    }
    admitted = !high && pcm->iac.hold[0] == 0 && pcm->iac.gear_hold == 0 && pcm->iac.ac_hold == 0 &&
        ((pcm->iac.context & 4u) || !(cal->options & 1u));
qualification:
    if (pcm->iac.low_battery || ((pcm->iac.kicker_flags & 4u) && pcm->iac.airflow == 0 && high)) admitted = false;
    if (!admitted) { pcm->iac.context &= (uint8_t)~8u;goto publish; }
    pcm->iac.context |= 8u;
    if (pcm->iac.context & 0x10u) {
        if (high) { pcm->iac.stall_hold = 0;commit = true;goto finish; }
    } else if (pcm->iac.stall_threshold > pcm->spark.rpm_high) {
        pcm->iac.context |= 0x10u;
        pcm->iac.stall_hold = cal->stall_hold[gear];
        integral = iac_add_high(integral, cal->stall_flow[pcm->iac.context & 3u]);
        commit = true;goto finish;
    }
    uint8_t error = pcm->iac.rpm_error;
    uint16_t increment = (uint16_t)pcm_lookup16(iac_error_coordinate(error), cal->integral_curve[2u * gear + high]) * error;
    uint8_t snapshot = ac ? bank->ac_snapshot : bank->no_ac_snapshot;
    if (!high) {
        if (pcm->reference.coolant > cal->reconcile_coolant && (integral >> 8) > cal->reconcile_flow[ac] &&
            !pcm->runtime.engine_service && !pcm->runtime.diagnostic_switch) {
            pcm->iac.state_flags &= (uint8_t)~4u;
            if (pcm->scheduler.phase < cal->reconcile_phase) --pcm->iac.position;
            goto publish;
        }
        if (pcm->iac.airflow == UINT16_MAX) goto publish;
        if (snapshot <= (integral >> 8) && cold < bank->bound) cold = iac_cap((uint32_t)cold + increment);
        else { integral = iac_cap((uint32_t)integral + increment);commit = true; }
    } else {
        uint8_t amount = pcm->iac.switch_adder;
        if (amount != 0) {
            uint8_t decrease = (uint8_t)(increment >> 8);
            pcm->iac.switch_adder = amount < decrease ? 0 : (uint8_t)(amount - (decrease ? decrease : 1u));
            goto publish;
        }
        amount = pcm->iac.startup_flow;
        if (amount != 0) {
            uint8_t decrease = (uint8_t)(increment >> 8);
            pcm->iac.startup_flow = amount < decrease ? 0 : (uint8_t)(amount - (decrease ? decrease : 1u));
            goto publish;
        }
        uint16_t candidate = integral < increment ? 0 : (uint16_t)(integral - increment);
        if (!(pcm->runtime.primary_faults & 0x10u) && cold != 0) {
            if ((candidate >> 8) < snapshot) { cold = cold < increment ? 0 : (uint16_t)(cold - increment);goto publish; }
        } else if (candidate == 0 && !(pcm->iac.state_flags & 0x40u) && error > cal->reconcile_error &&
                   !pcm->runtime.engine_service && !pcm->runtime.diagnostic_switch) {
            pcm->iac.state_flags &= (uint8_t)~4u;
            if (pcm->scheduler.phase < cal->reconcile_phase) ++pcm->iac.position;
        }
        integral = candidate;commit = true;
    }
finish:
    if (commit) {
        if (pcm->runtime.primary_faults & 0x10u) {
            uint8_t minimum = cal->default_integral[gear];
            if (ac) minimum = (uint8_t)(minimum + cal->default_ac_warm);
            if ((integral >> 8) < minimum) integral = (uint16_t)((uint16_t)minimum << 8);
        }
        if (ac) bank->ac = integral;else bank->no_ac = integral;
    }
publish:
    bank->cold = cold;pcm->iac.selected_cold = cold;
    pcm->iac.selected_bound = bank->bound;pcm->iac.selected_integral = integral;
    return PCM_OK;
}
