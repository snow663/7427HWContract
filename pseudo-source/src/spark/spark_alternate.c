#include "spark.h"
#include "hardware.h"
#include "reference_math.h"
/* AC51..ACA6 callable body. It deliberately retains083D and normal filters. */
PcmStatus pcm_spark_alternate(Pcm *pcm)
{
    if (pcm->spark.first_reference) {
        if (pcm->calibration == NULL || pcm->calibration->spark == NULL) return PCM_BAD_CONFIGURATION;
        const PcmSparkCalibration *cal = pcm->calibration->spark;
        uint16_t period;
        PcmStatus result = pcm_read16(pcm, PCM_REFERENCE_PERIOD, &period);
        if (result != PCM_OK) return result;
        pcm->spark.period_basis = period;
        pcm->spark.period = period;
        uint8_t multiplier = (uint8_t)(cal->period_scale * 32u);
        if (multiplier != 0) pcm->spark.period_basis = pcm_gain_word(pcm->spark.period_basis, multiplier);
        uint8_t low, rounded;
        (void)pcm_spark_coordinates(pcm->spark.period_basis, &low, &rounded);
        pcm->spark.rpm_low_coordinate = low;
        pcm->reference.rpm_coordinate = rounded;
    } else pcm->spark.period_basis = UINT16_MAX;
    pcm->spark.output_request = false;
    pcm->reference.consumed = false;
    return PCM_OK;
}
