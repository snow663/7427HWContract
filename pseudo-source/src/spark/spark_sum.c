#include "spark.h"
/* A7D7..A81D: incoming D is the just-stored EGR word. The callable C slice
 * consumes that producer-owned state; the word+128 rounding itself wraps. */
PcmStatus pcm_spark_sum(Pcm *pcm)
{
    if (pcm->calibration == NULL || pcm->calibration->spark == NULL) return PCM_BAD_CONFIGURATION;
    const PcmSparkCalibration *cal = pcm->calibration->spark;
    uint16_t sum = (uint16_t)((uint16_t)(pcm->spark.egr_filtered + 128u) >> 8);
    sum = (uint16_t)(sum + pcm->spark.altitude_advance);
    sum = (uint16_t)(sum + pcm->spark.base_advance);
    sum = (uint16_t)(sum + pcm->spark.pe_advance);
    sum = (uint16_t)(sum + pcm->spark.coolant_advance);
    sum = (uint16_t)(sum + pcm->spark.startup_adder);
    sum = (uint16_t)(sum - cal->base_bias);
    sum = (uint16_t)(sum - cal->coolant_bias);
    sum = (uint16_t)(sum - cal->altitude_bias);
    sum = (uint16_t)(sum - cal->egr_bias);
    if (pcm->spark.transmission_status & 0x0fu) sum = (uint16_t)(sum - cal->transmission_bias);
    sum = (uint16_t)(sum - pcm->knock.adaptive_retard);
    sum = (uint16_t)(sum - pcm->spark.transmission_retard);
    pcm->spark.composite = sum;
    return PCM_OK;
}
