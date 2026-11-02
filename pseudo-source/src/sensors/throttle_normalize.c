#include "board_io.h"
/* B1CF..B1EF. The rounded zero word wraps before its high byte is used. */
PcmStatus pcm_throttle_normalize(Pcm *pcm, uint8_t *result)
{
    if (pcm->calibration == NULL || pcm->calibration->air == NULL || result == NULL) return PCM_BAD_CONFIGURATION;
    uint16_t zero = (uint16_t)((uint16_t)pcm->iac.tps_zero_high * 256u + pcm->iac.tps_zero_low + 128u);
    uint8_t base = (uint8_t)(zero >> 8), raw = pcm->fuel.raw_throttle;
    uint8_t delta = raw < base ? 0 : (uint8_t)(raw - base);
    uint32_t scaled = ((uint32_t)delta * pcm->calibration->air->throttle_gain + 32u) * 4u;
    *result = scaled > 65535u ? 255u : (uint8_t)(scaled >> 8);
    pcm->fuel.normalized_throttle = *result;
    return PCM_OK;
}
