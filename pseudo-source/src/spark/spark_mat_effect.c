#include "spark.h"
#include "reference_math.h"
/* A81E..A84D: table interpolation rounds, but the magnitude product truncates.
 * The final sign gate is a second volatile flag sample after publishing083C. */
PcmStatus pcm_spark_mat_effect(Pcm *pcm)
{
    if (pcm->calibration == NULL || pcm->calibration->spark == NULL) return PCM_BAD_CONFIGURATION;
    uint8_t load = pcm->spark.load_coordinate;
    const PcmSparkCalibration *cal = pcm->calibration->spark;
    const uint8_t *curve = pcm->spark.mat_negative ? cal->mat_negative_gain : cal->mat_positive_gain;
    uint8_t coefficient = pcm_lookup16(load, curve);
    uint8_t effect = (uint8_t)(((uint16_t)coefficient * pcm->spark.mat_magnitude) >> 8);
    pcm->spark.mat_effect = effect;
    if (pcm->spark.mat_negative) pcm->spark.composite = (uint16_t)(pcm->spark.composite - pcm->spark.mat_effect);
    else pcm->spark.composite = (uint16_t)(pcm->spark.composite + effect);
    return PCM_OK;
}
