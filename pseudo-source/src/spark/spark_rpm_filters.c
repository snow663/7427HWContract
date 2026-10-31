#include "spark.h"
#include "reference_math.h"
/* A62A..A686. F479 exposes its intermediate0068 store; F436 only changes its
 * local frame before the0063 result. Existing paired RPM bytes stay shared. */
PcmStatus pcm_spark_rpm_filters(Pcm *pcm)
{
    if (pcm->calibration == NULL || pcm->calibration->spark == NULL) return PCM_BAD_CONFIGURATION;
    const PcmSparkCalibration *cal = pcm->calibration->spark;
    uint8_t rpm = pcm->reference.rpm_coordinate;
    uint16_t old = pcm->spark.rpm_monitor_filtered;
    uint16_t monitor = pcm_lag8(rpm, old, cal->monitor_filter_gain);
    pcm->spark.rpm_monitor_filtered = monitor;
    uint8_t rounded = (uint8_t)((uint16_t)(monitor + 128u) >> 8); /* Wrap, without SBCA correction. */
    if ((pcm->scheduler.phase & 0x1fu) == 4u) {
        pcm->spark.rpm_monitor_delta = (uint8_t)(rounded - pcm->spark.rpm_monitor_previous);
        pcm->spark.rpm_monitor_previous = rounded;
    }
    uint32_t coordinate = ((uint32_t)pcm->spark.rpm_raw * 4u + 128u) >> 8;
    uint8_t load = coordinate > 255u ? 255u : (uint8_t)coordinate;
    pcm->reference.load_coordinate = load;
    uint16_t target = (uint16_t)((uint16_t)load << 8);
    old = pcm->reference.load_filtered;
    if (old != 0) {
        uint16_t intermediate;
        uint16_t filtered = pcm_lag16(target, old, cal->load_filter_gain, &intermediate);
        pcm->reference.load_filtered = intermediate;
        pcm->reference.load_filtered = filtered;
    } else pcm->reference.load_filtered = target;
    uint32_t doubled = (uint32_t)pcm->spark.rpm_raw * 2u;
    target = doubled > 65535u ? UINT16_MAX : (uint16_t)doubled;
    pcm->spark.transient_target = (uint8_t)(target >> 8);
    old = (uint16_t)((uint16_t)pcm->spark.rpm_high * 256u + pcm->spark.rpm_fraction);
    uint16_t filtered = old == 0 ? target : pcm_lag16(target, old, cal->rpm_filter_gain, NULL);
    pcm->spark.rpm_high = (uint8_t)(filtered >> 8);
    pcm->spark.rpm_fraction = (uint8_t)filtered;
    return PCM_OK;
}
