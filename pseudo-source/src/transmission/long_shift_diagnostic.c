#include "control.h"
#include "../system/system_internal.h"

/* $F131..$F1DC. Diagnosis compares signed CBA operands after the biased
 * table lookup. The ASLA sequence saturates to FF on the first carry. */
PcmStatus pcm_long_shift_diagnostic(Pcm *pcm)
{
    uint8_t flags, count, limit;
    if (pcm->runtime.monitor_freeze) return PCM_OK;
    SYS_RUN(pcm_read8(pcm, 0x5b08, &flags));
    if (!(flags & 4u)) return PCM_OK;
    SYS_RUN(pcm_read8(pcm, 0x96, &flags));
    if (!(flags & 0x40u)) {
        SYS_RUN(pcm_update8(pcm, 0x96, 0, 0x40));
        SYS_RUN(pcm_read8(pcm, 0x1e, &flags));
        if (!(flags & 4u)) return PCM_OK;
        SYS_RUN(pcm_read8(pcm, 0x31, &count));
        SYS_RUN(pcm_read8(pcm, 0x5bca, &limit));
        if (count >= limit) return PCM_OK;
        SYS_RUN(pcm_write8(pcm, 0x31, (uint8_t)(count + 2u)));
        return pcm_update8(pcm, 0x1e, 4, 0);
    }
    SYS_RUN(pcm_read8(pcm, 0x1e, &flags));
    if (flags & 4u) return PCM_OK;
    uint8_t sample, gear, throttle, threshold;
    uint16_t curve;
    SYS_RUN(pcm_read8(pcm, 0x148, &sample));
    uint8_t scaled = sample >= 32u ? 255u : (uint8_t)(sample << 3);
    SYS_RUN(pcm_read8(pcm, 0xd9, &gear));
    uint8_t index = (uint8_t)(gear - 1u);
    if (index & 0x80u) return PCM_OK;
    SYS_RUN(pcm_read16(pcm, (uint16_t)(0xbc6bu + (uint8_t)(index << 1)), &curve));
    SYS_RUN(pcm_read8(pcm, 0xb2, &throttle));
    SYS_RUN(sys_curve16(pcm, throttle, curve, &threshold));
    int signed_scaled = scaled < 128u ? (int)scaled : (int)scaled - 256;
    if ((int)threshold - 128 > signed_scaled) return PCM_OK;

    SYS_RUN(pcm_read8(pcm, 0xd9, &gear));
    if (gear < 1u || gear > 3u) return PCM_OK;
    index = gear - 1u;
    SYS_RUN(pcm_read8(pcm, 0x136u + index, &sample));
    SYS_RUN(pcm_read8(pcm, 0x5bc4u + index, &limit));
    if (sample <= limit) return PCM_OK;
    bool admitted;
    SYS_RUN(pcm_long_shift_qualification(pcm, 0x5b00, &admitted));
    if (!admitted) return PCM_OK;
    SYS_RUN(pcm_read8(pcm, 0x32u + index, &count));
    count = (uint8_t)(count + 1u);
    SYS_RUN(pcm_read8(pcm, 0x5bc7u + index, &limit));
    if (count >= limit) return pcm_update8(pcm, 0x1e, 0, 4);
    return pcm_write8(pcm, 0x32u + index, count);
}
