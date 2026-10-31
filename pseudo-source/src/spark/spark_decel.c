#include "spark.h"
#include "reference_math.h"
/* A97A..A9DF. The startup/recovery word is shared, not a new independent lag. */
PcmStatus pcm_spark_decel(Pcm *pcm)
{
    if (pcm->calibration == NULL || pcm->calibration->spark == NULL) return PCM_BAD_CONFIGURATION;
    const PcmSparkCalibration *cal = pcm->calibration->spark;
    if (pcm->runtime.deceleration_fuel_cut) {
        pcm->spark.recovery_active = true;
        pcm->spark.startup_recovery_gain = 0;
        uint8_t amount = cal->decel_base;
        uint8_t difference = (uint8_t)(pcm->spark.coolant_advance - cal->coolant_bias);
        if (!(difference & 0x80u)) amount = (uint8_t)(amount + difference);
        pcm->spark.decel_retard = amount;
        uint16_t command = pcm->spark.composite;
        pcm->spark.composite = (uint16_t)(command - pcm->spark.decel_retard);
    } else if (pcm->spark.recovery_active) {
        uint8_t gain = cal->recovery_gain;
        if (pcm->reference.throttle > cal->recovery_throttle) gain = cal->recovery_fast_gain;
        uint16_t old = pcm->spark.startup_recovery_gain;
        if (old > 0xfef0u) pcm->spark.recovery_active = false;
        else pcm->spark.startup_recovery_gain = pcm_lag8(255, old, gain);
        uint8_t amount = pcm->spark.decel_retard;
        uint8_t high = (uint8_t)(pcm->spark.startup_recovery_gain >> 8);
        uint8_t recovery = (uint8_t)(((uint16_t)high * amount + 128u) >> 8);
        uint16_t command = pcm->spark.composite;
        command = (uint16_t)(command + recovery);
        pcm->spark.composite = (uint16_t)(command - pcm->spark.decel_retard);
    }
    return PCM_OK;
}
