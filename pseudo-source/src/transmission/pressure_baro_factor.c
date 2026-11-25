#include "control.h"
#include "../system/system_internal.h"

/* $D969..$D97F. X supplies the scalar address. The final BGT observes
 * the signed high-byte addition, then ASLD doubles the retained word. */
PcmStatus pcm_pressure_baro_factor(Pcm *pcm, uint16_t scalar, uint16_t *result)
{
    if (pcm == NULL || result == NULL) return PCM_BAD_CONFIGURATION;
    uint8_t baro, gain;
    SYS_RUN(pcm_read8(pcm, 0xac, &baro));
    SYS_RUN(pcm_read8(pcm, scalar, &gain));
    uint16_t product = (uint16_t)(uint8_t)(baro - 128u) * (uint16_t)gain;
    SYS_RUN(pcm_read8(pcm, 0xac, &baro));
    if (!(baro & 0x80u)) {
        SYS_RUN(pcm_read8(pcm, scalar, &gain));
        product = (uint16_t)(product - (uint16_t)gain * 256u);
    }
    int high = product >> 8;
    if (high >= 128) high -= 256;
    *result = high + 64 > 0 ? (uint16_t)((product + 0x4000u) << 1) : 0;
    return PCM_OK;
}
