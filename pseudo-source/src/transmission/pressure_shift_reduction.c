#include "control.h"
#include "../system/system_internal.h"

/* $BC77..$BCC5. PULA preserves the zero flag from the timer store at
 * $BCB6. The SUBA overflow path uses its original unsigned borrow. */
PcmStatus pcm_pressure_shift_reduction(Pcm *pcm, uint8_t pressure, uint8_t *result)
{
    if (pcm == NULL || result == NULL) return PCM_BAD_CONFIGURATION;
    uint8_t timer, events, gear, reduction;
    uint16_t ratio, threshold, pair = 0;
    SYS_RUN(pcm_read8(pcm, 0x198, &timer));
    if (timer) --timer;
    SYS_RUN(pcm_read16(pcm, 0xf9, &ratio));
    SYS_RUN(pcm_read8(pcm, 0x83, &events));
    if (events & 3u) {
        SYS_RUN(pcm_read8(pcm, 0xd9, &gear));
        if (gear == 2u || gear == 3u) {
            SYS_RUN(pcm_read16(pcm, 0x68af, &threshold));
            if (ratio > threshold) pair = gear == 2u ? 0x5f06 : 0x5f08;
            else if (gear == 3u) {
                SYS_RUN(pcm_read16(pcm, 0x68b1, &threshold));
                if (ratio > threshold) pair = 0x5f0a;
            }
        }
    }
    if (pair) {
        SYS_RUN(pcm_read8(pcm, pair, &timer));
        SYS_RUN(pcm_read8(pcm, pair + 1u, &reduction));
        SYS_RUN(pcm_write8(pcm, 0x199, reduction));
    }
    SYS_RUN(pcm_write8(pcm, 0x198, timer));
    if (timer) {
        SYS_RUN(pcm_read8(pcm, 0x199, &reduction));
        uint8_t difference = (uint8_t)(pressure - reduction);
        if ((pressure ^ reduction) & (pressure ^ difference) & 0x80u)
            difference = (uint8_t)(127u + (pressure < reduction));
        pressure = difference;
    }
    *result = pressure;
    return PCM_OK;
}
