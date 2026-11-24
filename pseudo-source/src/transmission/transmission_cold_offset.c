#include "gear_internal.h"
#include "reference_math.h"

/* D980..D9B6. F550 rounds the magnitude before the original sign is
 * restored and the addition is limited to the unsigned word range. */
PcmStatus pcm_transmission_cold_offset(Pcm *pcm, uint16_t base, uint16_t offset, uint16_t *result)
{
    if (pcm == NULL || result == NULL) return PCM_BAD_CONFIGURATION;
    uint8_t gain;
    SYS_RUN(pcm_read8(pcm, 0x00ab, &gain));
    bool subtract = (offset & 0x8000u) != 0;
    uint16_t magnitude = subtract ? (uint16_t)(0u - offset) : offset;
    uint16_t correction = pcm_gain_word(magnitude, gain);
    if (subtract) {
        *result = base < correction ? 0 : (uint16_t)(base - correction);
    } else {
        uint32_t sum = (uint32_t)base + correction;
        *result = sum > UINT16_MAX ? UINT16_MAX : (uint16_t)sum;
    }
    return PCM_OK;
}
