#include "iac.h"
#include "reference_math.h"
/* 969E..9748. The steering bit0036.5 is cleared even on the seeded route. */
PcmStatus pcm_iac_error(Pcm *pcm)
{
    if (pcm->calibration == NULL || pcm->calibration->iac == NULL) return PCM_BAD_CONFIGURATION;
    const PcmIacCalibration *cal = pcm->calibration->iac;
    if (cal->output_options & 2u) {
        if (!(pcm->iac.input_shadow & 0x80u)) {
            pcm->spark.override_request = true;
            pcm->iac.switch_adder = cal->steering_flow;pcm->iac.switch_hold = cal->switch_decay_reload;
            pcm->iac.qualification_delay = cal->steering_delay;
        }
        pcm->spark.override_request = false;
    }
    if (pcm->iac.gear_hold == 0) pcm->iac.gear_adder = 0;else --pcm->iac.gear_hold;
    if (pcm->iac.ac_hold != 0) --pcm->iac.ac_hold;
    if (pcm->iac.stall_hold == 0) pcm->iac.context &= (uint8_t)~0x10u;else --pcm->iac.stall_hold;
    if (pcm->iac.follower_hold != 0) --pcm->iac.follower_hold;
    uint8_t rpm = pcm->spark.rpm_high, target = pcm->spark.iac_desired_speed;
    uint8_t error;
    if (rpm >= target) { pcm->iac.context |= 0x80u;error = (uint8_t)(rpm - target); }
    else { pcm->iac.context &= (uint8_t)~0x80u;error = (uint8_t)(target - rpm); }
    pcm->iac.rpm_error = error;
    uint8_t forced = 0;
    if (pcm->iac.gear_hold != 0) forced = cal->error_deadband[1];
    if (pcm->iac.ac_hold != 0 && forced < cal->error_deadband[2]) forced = cal->error_deadband[2];
    if (pcm->iac.switch_hold != 0 && forced < cal->error_deadband[3]) forced = cal->error_deadband[3];
    if ((pcm->iac.follower_filtered >> 8) > pcm->iac.follower_closed_threshold && forced < cal->error_deadband[0]) forced = cal->error_deadband[0];
    pcm->iac.rpm_error_filtered = forced ? (uint16_t)((uint16_t)forced << 8) : pcm_lag8(error, pcm->iac.rpm_error_filtered, cal->error_gain);
    return PCM_OK;
}
