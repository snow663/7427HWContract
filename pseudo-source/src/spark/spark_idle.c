#include "spark.h"
#include "reference_math.h"
/* A84E..A905. Difference direction follows SUBD's unsigned borrow, not N. */
PcmStatus pcm_spark_idle(Pcm *pcm)
{
    if (pcm->calibration == NULL || pcm->calibration->spark == NULL) return PCM_BAD_CONFIGURATION;
    const PcmSparkCalibration *cal = pcm->calibration->spark;
    if (pcm->scheduler.run_counter < cal->idle_runtime_minimum ||
        pcm->spark.vehicle_speed_high >= cal->idle_speed_limit) goto disable;
    uint8_t throttle_limit = cal->idle_throttle_entry;
    if (pcm->spark.idle_feedback) throttle_limit = cal->idle_throttle_retained;
    if (throttle_limit <= pcm->reference.throttle || pcm->reference.coolant <= cal->idle_coolant_minimum) goto disable;
    uint8_t target = pcm->spark.iac_desired_speed;
    if (!pcm->spark.idle_state) {
        uint16_t adjusted = (uint16_t)target + cal->idle_target_adder;
        if (adjusted > 255u) { pcm->spark.idle_negative = false;goto disable; }
        target = (uint8_t)adjusted;
    }
    uint16_t desired = (uint16_t)target << 8;
    uint16_t rpm = (uint16_t)pcm->spark.rpm_high << 8;
    rpm = (uint16_t)(rpm + pcm->spark.rpm_fraction);
    bool negative = desired < rpm;
    pcm->spark.idle_negative = negative;
    uint16_t difference = negative ? (uint16_t)(rpm - desired) : (uint16_t)(desired - rpm);
    uint16_t coordinate = difference < 1024u ? (difference >> 4) : (uint16_t)((difference >> 7) + 56u);
    uint8_t index = coordinate > 255u ? 255u : (uint8_t)coordinate;
    const PcmCappedCurve *speed = negative ? &cal->idle_negative_speed : &cal->idle_positive_speed;
    const PcmCappedCurve *load = negative ? &cal->idle_negative_load : &cal->idle_positive_load;
    uint8_t speed_value,load_value;
    PcmStatus result = pcm_lookup_capped(index, speed, &speed_value);
    if (result != PCM_OK) return result;
    result = pcm_lookup_capped(pcm->spark.load_coordinate, load, &load_value);
    if (result != PCM_OK) return result;
    uint8_t amplitude = (uint8_t)(((uint16_t)speed_value * load_value) >> 8);
    if (pcm->spark.idle_negative) amplitude = (uint8_t)(0u - amplitude);
    uint8_t derivative = pcm->spark.idle_derivative;
    derivative = derivative >= 96u ? (uint8_t)(derivative - 96u) : 0;
    if (derivative > 63u) derivative = 63;
    uint8_t correction = pcm_lookup16((uint8_t)(derivative * 4u), cal->idle_derivative_curve);
    correction = (uint8_t)(correction + amplitude - cal->idle_bias);
    uint16_t signed_word;
    if (correction & 0x80u) signed_word = (uint16_t)(0xff00u | correction);
    else {
        if (correction > cal->idle_positive_cap) correction = cal->idle_positive_cap;
        signed_word = correction;
    }
    pcm->spark.composite = (uint16_t)(signed_word + pcm->spark.composite);
    pcm->spark.idle_feedback = true;
    return PCM_OK;
disable:
    pcm->spark.idle_feedback = false;
    return PCM_OK;
}
