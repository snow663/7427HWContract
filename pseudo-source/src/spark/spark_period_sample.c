#include "spark.h"
#include "hardware.h"
#include "reference_math.h"
/* A5E5..A629: unscaled period retained separately, wrapped divisor doubling,
 * piecewise low-RPM coordinate and saturating rounded ordinary coordinate. */
PcmStatus pcm_spark_period_sample(Pcm *pcm)
{
    if (pcm->calibration == NULL || pcm->calibration->spark == NULL) return PCM_BAD_CONFIGURATION;
    uint16_t period;
    PcmStatus result = pcm_read16(pcm, PCM_REFERENCE_PERIOD, &period);
    if (result != PCM_OK) return result;
    pcm->spark.period_basis = period;
    pcm->spark.period = period;
    uint8_t multiplier = (uint8_t)(pcm->calibration->spark->period_scale * 32u);
    if (multiplier != 0) pcm->spark.period_basis = pcm_gain_word(pcm->spark.period_basis, multiplier);
    uint8_t low, rounded;
    uint16_t rpm = pcm_spark_coordinates(pcm->spark.period_basis, &low, &rounded);
    pcm->spark.rpm_raw = rpm;
    pcm->spark.rpm_low_coordinate = low;
    pcm->reference.rpm_coordinate = rounded;
    return PCM_OK;
}
