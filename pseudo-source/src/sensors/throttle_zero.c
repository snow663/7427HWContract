#include "board_io.h"
#include "reference_math.h"
/* B1AC..B1CE. F436's target includes the literal80 fractional byte. */
PcmStatus pcm_throttle_zero(Pcm *pcm)
{
    uint8_t raw = pcm->fuel.raw_throttle;
    if (raw <= pcm->iac.tps_zero_high) return PCM_OK;
    if (pcm->calibration == NULL || pcm->calibration->air == NULL) return PCM_BAD_CONFIGURATION;
    const PcmAirCalibration *cal = pcm->calibration->air;
    uint16_t old = (uint16_t)((uint16_t)pcm->iac.tps_zero_high * 256u + pcm->iac.tps_zero_low);
    uint16_t value = pcm_lag16((uint16_t)((uint16_t)raw * 256u + 128u), old, cal->throttle_zero_gain, NULL);
    pcm->iac.tps_zero_high = (uint8_t)(value >> 8);
    pcm->iac.tps_zero_low = (uint8_t)value;
    if ((value >> 8) >= cal->throttle_zero_minimum) {
        pcm->iac.tps_zero_high = cal->throttle_zero_minimum;
        pcm->iac.tps_zero_low = 0;
    }
    return PCM_OK;
}
