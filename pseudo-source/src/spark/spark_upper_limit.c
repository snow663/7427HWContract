#include "spark.h"
/* AA1A..AA32: byte reference subtraction wraps, then a true signed BGT cap.
 * XOR8000 gives the signed16 ordering without a narrowing signed cast. */
PcmStatus pcm_spark_upper_limit(Pcm *pcm)
{
    if (pcm->calibration == NULL || pcm->calibration->spark == NULL) return PCM_BAD_CONFIGURATION;
    const PcmSparkCalibration *cal = pcm->calibration->spark;
    pcm->spark.command = (uint16_t)(pcm->spark.composite - cal->reference_bias);
    uint16_t bound = cal->upper_limit;
    uint16_t command = pcm->spark.command;
    if ((uint16_t)(bound ^ 0x8000u) <= (uint16_t)(command ^ 0x8000u)) pcm->spark.command = bound;
    return PCM_OK;
}
