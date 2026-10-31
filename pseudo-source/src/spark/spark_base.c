#include "spark.h"
#include "reference_math.h"
/* A700..A72C: two history latches, retained idle-table selector and piecewise RPM. */
PcmStatus pcm_spark_base(Pcm *pcm)
{
    if (pcm->calibration == NULL || pcm->calibration->spark == NULL) return PCM_BAD_CONFIGURATION;
    pcm->spark.previous_load = pcm->spark.recent_load;
    pcm->spark.recent_load = pcm->spark.load_coordinate;
    const PcmSparkCalibration *cal = pcm->calibration->spark;
    const PcmTable2D *table = pcm->spark.idle_feedback ? &cal->base_idle : &cal->base_normal;
    uint8_t load = pcm->spark.load_coordinate;
    uint8_t rpm = pcm->spark.rpm_low_coordinate;
    if (rpm > 64u) {
        uint16_t sum = (uint16_t)pcm->reference.rpm_coordinate + 16u;
        rpm = sum > 255u ? 255u : (uint8_t)sum;
    }
    uint8_t result;
    PcmStatus status = pcm_lookup2d(rpm, load, table, &result);
    if (status == PCM_OK) pcm->spark.base_advance = result;
    return status;
}
