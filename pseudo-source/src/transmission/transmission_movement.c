#include "control.h"
#include "../system/system_internal.h"

/* $B334..$B366. Each threshold comparison is unsigned, including equality.
 * The counter wraps before its fresh comparison with the delay calibration. */
PcmStatus pcm_transmission_movement(Pcm *pcm)
{
    static const uint16_t signals[] = {0x01ac, 0x00d3, 0x00c6};
    for (unsigned i = 0; i < 3; ++i) {
        uint16_t sample, limit;
        SYS_RUN(pcm_read16(pcm, signals[i], &sample));
        SYS_RUN(pcm_read16(pcm, (uint16_t)(0x5d23u + 2u*i), &limit));
        if (sample >= limit) {
            SYS_RUN(pcm_write8(pcm, 0x00ff, 0));
            return pcm_update8(pcm, 0x0086, 0, 0x80u);
        }
    }
    uint8_t flags, count, delay;
    SYS_RUN(pcm_read8(pcm, 0x0086, &flags));
    if (!(flags & 0x80u)) return PCM_OK;
    SYS_RUN(pcm_read8(pcm, 0x00ff, &count));
    SYS_RUN(pcm_write8(pcm, 0x00ff, (uint8_t)(count + 1u)));
    SYS_RUN(pcm_read8(pcm, 0x5d0e, &delay));
    SYS_RUN(pcm_read8(pcm, 0x00ff, &count));
    if (delay < count) return pcm_update8(pcm, 0x0086, 0x80u, 0);
    return PCM_OK;
}
