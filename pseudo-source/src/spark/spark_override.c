#include "spark.h"
/* A9E7..AA19: disabled retains the latch; enabled failed admission clears it. */
PcmStatus pcm_spark_override(Pcm *pcm)
{
    if (pcm->calibration == NULL || pcm->calibration->spark == NULL) return PCM_BAD_CONFIGURATION;
    const PcmSparkCalibration *cal = pcm->calibration->spark;
    if (!(cal->override_options & 0x02u)) return PCM_OK;
    if (pcm->spark.override_request && pcm->reference.coolant > cal->override_coolant_minimum) {
        uint8_t throttle = pcm->reference.throttle;
        uint8_t limit = pcm->spark.override_active ? cal->override_throttle_retained : cal->override_throttle_entry;
        if (throttle <= limit) {
            pcm->spark.composite = cal->override_command;
            pcm->spark.override_active = true;
            return PCM_OK;
        }
    }
    pcm->spark.override_active = false;
    return PCM_OK;
}
