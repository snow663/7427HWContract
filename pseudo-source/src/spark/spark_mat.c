#include "spark.h"
#include "reference_math.h"
/* CA6B..CAB3: disabled/cold paths zero magnitude and retain the old sign. */
PcmStatus pcm_spark_mat(Pcm *pcm)
{
    if (pcm->calibration == NULL || pcm->calibration->spark == NULL) return PCM_BAD_CONFIGURATION;
    const PcmSparkCalibration *cal = pcm->calibration->spark;
    uint8_t magnitude = 0;
    if (pcm->calibration->reference.mode_b & 0x40u) {
        uint8_t row = pcm->spark.mat_sample;
        if (row >= 80u) {
            if (row > 192u) row = 192;
            uint8_t column;
            if (cal->mat_mode) {
                column = pcm->reference.rpm_coordinate;
                if (column > 176u) column = 176;
            } else {
                column = pcm->spark.vacuum;
                column = column >= 80u ? (uint8_t)(column - 80u) : 0;
            }
            uint8_t result;
            PcmStatus status = pcm_lookup2d(row, column, &cal->mat, &result);
            if (status != PCM_OK) return status;
            uint8_t difference = (uint8_t)(result - cal->mat_bias);
            if (difference & 0x80u) {
                pcm->spark.mat_negative = true;
                magnitude = (uint8_t)(0u - difference);
            } else {
                pcm->spark.mat_negative = false;
                magnitude = difference;
            }
        }
    }
    pcm->spark.mat_magnitude = magnitude;
    return PCM_OK;
}
