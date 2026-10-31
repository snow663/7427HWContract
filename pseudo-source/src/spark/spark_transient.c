#include "spark.h"
#include "reference_math.h"
/* A906..A979: error is committed before the word filter changes its baseline. */
PcmStatus pcm_spark_transient(Pcm *pcm)
{
    if (pcm->calibration == NULL || pcm->calibration->spark == NULL) return PCM_BAD_CONFIGURATION;
    const PcmSparkCalibration *cal = pcm->calibration->spark;
    uint8_t coolant = pcm->reference.coolant;
    if (coolant < cal->transient_coolant_minimum || coolant > cal->transient_coolant_maximum ||
        !(pcm->calibration->mode_f & 0x80u)) return PCM_OK;
    if (pcm->spark.idle_state) {
        pcm->spark.transient_filtered = (uint16_t)pcm->spark.transient_target << 8;
        return PCM_OK;
    }
    uint8_t rpm = pcm->spark.rpm_high;
    pcm->spark.transient_error = (uint8_t)(rpm - (pcm->spark.transient_filtered >> 8));
    uint8_t gain = pcm_lookup16((uint8_t)(pcm->reference.throttle >> 2), cal->transient_gain);
    uint8_t target = pcm->spark.transient_target;
    uint16_t old = pcm->spark.transient_filtered;
    pcm->spark.transient_filtered = pcm_lag8(target, old, gain);
    uint8_t error = pcm->spark.transient_error;
    const uint8_t *parameters = (error & 0x80u) ? cal->transient_negative : cal->transient_positive;
    uint8_t magnitude = (error & 0x80u) ? (uint8_t)(0u - error) : error;
    uint8_t correction = (uint8_t)((((uint16_t)magnitude * parameters[0]) >> 8) + parameters[1]);
    if (correction > parameters[2]) correction = parameters[2];
    pcm->spark.transient_correction = correction;
    bool negative = (pcm->spark.transient_error & 0x80u) != 0;
    uint16_t command = pcm->spark.composite;
    uint8_t amount = pcm->spark.transient_correction;
    pcm->spark.composite = negative ? (uint16_t)(command + amount) : (uint16_t)(command - amount);
    return PCM_OK;
}
