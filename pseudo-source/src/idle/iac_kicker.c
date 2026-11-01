#include "iac.h"
/* 9EEA..9FDD. Ordered kicker qualification and phase07 timer routes. */
PcmStatus pcm_iac_kicker(Pcm *pcm)
{
    if (pcm->calibration == NULL || pcm->calibration->iac == NULL) return PCM_BAD_CONFIGURATION;
    const PcmIacCalibration *cal = pcm->calibration->iac;
    if (!(cal->options & 4u) || (pcm->runtime.engine_service && pcm->iac.service_kicker)) return PCM_OK;
    if (pcm->iac.kicker_flags & 4u) {
        if ((pcm->iac.context & 0x0cu) == 0x0cu) {
            pcm->iac.baseline_on = pcm->iac.tps_zero_high;
            pcm->iac.learning_flags |= 1u;
        }
        if (pcm->iac.kicker_flags & 8u) goto timer;
        if (pcm->reference.coolant < cal->kicker_coolant_minimum) {
            pcm->iac.kicker_timer = cal->kicker_cold_reload;
            return pcm_iac_kicker_enable(pcm);
        }
        if (pcm->iac.kicker_flags & 0x10u) goto timer;
        if (pcm->spark.barometric_high >= cal->kicker_baro_entry) goto timer;
        if (!(pcm->iac.context & 0x80u) ||
            (uint8_t)(pcm->iac.bank[1].no_ac >> 8) >= cal->kicker_integral_limit || !(pcm->iac.context & 8u)) return PCM_OK;
        if (cal->kicker_error_limit[(pcm->iac.context & 2u) != 0] > pcm->iac.rpm_error)
            pcm->iac.kicker_flags |= 0x10u;
timer:
        if ((pcm->iac.context & 0x40u) && pcm->iac.kicker_timer != 0) goto decrement;
        if (pcm->reference.throttle > cal->kicker_throttle_limit || pcm->spark.vehicle_speed_high > cal->kicker_speed_limit) goto decision;
        if (pcm->iac.context & 0x40u) return pcm_iac_kicker_enable(pcm);
        if (pcm->iac.kicker_timer == 0) goto decision;
decrement:
        if ((pcm->scheduler.phase & 0xf0u) == 0) --pcm->iac.kicker_timer;
        return pcm_iac_kicker_enable(pcm);
    }
    if (pcm->iac.kicker_timer > 15u) {
        if ((pcm->iac.context & 0x0cu) == 0x0cu) {
            pcm->iac.baseline_off = pcm->iac.tps_zero_high;
            pcm->iac.learning_flags |= 2u;
        }
        if (pcm->iac.kicker_timer == cal->kicker_off_match) goto decision;
    }
    if ((pcm->scheduler.phase & 0xf0u) == 0) ++pcm->iac.kicker_timer;
    return pcm_iac_kicker_disable(pcm);
decision:
    if (pcm->spark.barometric_high <= cal->kicker_baro_exit ||
        (uint8_t)((uint16_t)(pcm->iac.bank[1].no_ac + pcm->iac.bank[1].cold) >> 8) > cal->kicker_flow_limit) {
        if (pcm->reference.throttle > cal->kicker_throttle_limit || pcm->spark.vehicle_speed_high > cal->kicker_speed_limit)
            return pcm_iac_kicker_enable(pcm);
        return PCM_OK;
    }
    return pcm_iac_kicker_disable(pcm);
}
