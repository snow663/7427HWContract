#include "knock.h"
/* AA33..AA80: optional burst latch/countdown and wrapped command subtraction. */
PcmStatus pcm_knock_burst(Pcm *pcm)
{
    if (pcm->calibration == NULL) return PCM_BAD_CONFIGURATION;
    const PcmKnockCalibration *cal = &pcm->calibration->knock;
    if (!(pcm->calibration->mode_f & 0x08u) || pcm->runtime.diagnostic_switch ||
        pcm->reference.coolant <= cal->minimum_coolant) return PCM_OK;
    if (pcm->knock.burst_active) {
        --pcm->knock.burst_countdown; /* Zero wraps to255. */
        if (pcm->knock.burst_countdown == 0) pcm->knock.burst_active = false;
        pcm->spark.command = (uint16_t)(pcm->spark.command - pcm->knock.burst_gain);
    } else {
        if (pcm->spark.load_coordinate >= cal->burst_load_limit) return PCM_OK;
        uint8_t throttle = pcm->reference.throttle;
        if (throttle >= cal->burst_throttle_limit) return PCM_OK;
        uint8_t previous = pcm->spark.previous_throttle;
        if (throttle < previous || (uint8_t)(throttle - previous) < cal->burst_throttle_delta) return PCM_OK;
        pcm->knock.burst_active = true;
        pcm->knock.burst_countdown = cal->burst_duration;
    }
    return PCM_OK;
}
