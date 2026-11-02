#include "iac.h"
#include "reference_math.h"
/* 9CA6..9CFC: equal high bytes retain the fraction, sign and magnitude. */
PcmStatus pcm_iac_derivative(Pcm *pcm)
{
    if (pcm->calibration == NULL || pcm->calibration->iac == NULL) return PCM_BAD_CONFIGURATION;
    const PcmIacCalibration *cal = pcm->calibration->iac;
    uint8_t ratio = pcm->spark.idle_derivative;
    uint8_t coordinate = ratio < 96u ? 0 : ratio >= 160u ? 255 : (uint8_t)(4u * (ratio - 96u));
    uint8_t target = pcm_lookup16(coordinate, cal->derivative_curve);
    uint16_t old = pcm->iac.derivative_filtered;
    uint8_t previous = (uint8_t)(old >> 8);
    if (target == previous) return PCM_OK;
    bool high = (pcm->iac.context & 0x80u) != 0, positive = (pcm->iac.kicker_flags & 0x80u) != 0;
    uint16_t next;
    if (positive && (target < previous || high)) next = pcm_lag8(target, old, cal->derivative_fast_gain);
    else if (!positive && (target > previous || !high)) next = pcm_lag8(target, old, cal->derivative_slow_gain);
    else next = (uint16_t)((uint16_t)target << 8);
    pcm->iac.derivative_filtered = next;
    uint8_t byte = (uint8_t)(next >> 8), magnitude;
    if (byte < 128u) { pcm->iac.kicker_flags &= (uint8_t)~0x80u;magnitude = (uint8_t)(128u - byte); }
    else { pcm->iac.kicker_flags |= 0x80u;magnitude = (uint8_t)(byte - 128u); }
    pcm->iac.derivative = (uint8_t)((magnitude + 2u) >> 2);
    return PCM_OK;
}
