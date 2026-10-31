#include "spark.h"
#include "reference_math.h"
/* A72D..A763. The cold-idle floor rereads coolant after the table lookup. */
PcmStatus pcm_spark_coolant(Pcm *pcm)
{
    if (pcm->calibration == NULL || pcm->calibration->spark == NULL) return PCM_BAD_CONFIGURATION;
    const PcmSparkCalibration *cal = pcm->calibration->spark;
    uint8_t column = pcm->spark.vacuum;
    if (cal->coolant_mode) column = pcm->spark.load_coordinate;
    column >>= 1;
    uint8_t row = pcm->reference.coolant;
    if (row > 176u) { if (row > 208u) row = 208;row = (uint8_t)((row - 88u) * 2u); }
    uint8_t result;
    PcmStatus status = pcm_lookup2d(row, column, &cal->coolant, &result);
    if (status != PCM_OK) return status;
    if (pcm->spark.idle_state && pcm->reference.coolant < cal->idle_coolant_threshold && result < cal->coolant_bias)
        result = cal->coolant_bias;
    pcm->spark.coolant_advance = result;
    return PCM_OK;
}
