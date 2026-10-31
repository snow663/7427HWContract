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
    uint16_t divisor = (uint16_t)(pcm->spark.period_basis * 2u);
    uint16_t rpm = divisor <= 307u ? UINT16_MAX : (uint16_t)((307UL << 16) / divisor);
    pcm->spark.rpm_raw = rpm;
    uint32_t low;
    if (rpm >= 0x6000u) {
        low = (uint32_t)rpm + 0x4080u;
        pcm->spark.rpm_low_coordinate = low > 65535u ? 255u : (uint8_t)(low >> 8);
    } else {
        low = (uint32_t)rpm * 2u;
        pcm->spark.rpm_low_coordinate = low < 0x1f80u ? 0u : (uint8_t)((low - 0x1f80u) >> 8);
    }
    uint16_t rounded = (uint16_t)(((uint32_t)rpm + 128u) >> 8);
    pcm->reference.rpm_coordinate = rounded > 255u ? 255u : (uint8_t)rounded;
    return PCM_OK;
}
