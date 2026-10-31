#include "spark.h"
#include "reference_math.h"
/* A792..A7D6: reset to bias when inactive; retained word lag when active. */
PcmStatus pcm_spark_egr(Pcm *pcm)
{
    if (pcm->calibration == NULL || pcm->calibration->spark == NULL) return PCM_BAD_CONFIGURATION;
    const PcmSparkCalibration *cal = pcm->calibration->spark;
    uint16_t word = (uint16_t)cal->egr_bias << 8;
    if (pcm->spark.egr_active) {
        uint8_t column = (uint8_t)(((uint16_t)192u * pcm->spark.egr_fraction_high) >> 8);
        if (cal->egr_mode) {
            uint8_t vacuum = (uint8_t)(0u - pcm->spark.vacuum);
            if (vacuum <= 64u) column = (uint8_t)(vacuum * 2u);
            else {
                uint8_t transformed = (uint8_t)(((vacuum - 64u) >> 1) + 128u);
                column = transformed > 192u ? 192u : transformed;
            }
        }
        uint8_t row = pcm->reference.rpm_coordinate;
        if (row > 160u) row = 160;
        uint8_t target;
        PcmStatus status = pcm_lookup2d((uint8_t)(row >> 1), column, &cal->egr, &target);
        if (status != PCM_OK) return status;
        uint8_t gain = cal->egr_gain;
        uint16_t old = pcm->spark.egr_filtered;
        word = pcm_lag8(target, old, gain);
    }
    pcm->spark.egr_filtered = word;
    return PCM_OK;
}
