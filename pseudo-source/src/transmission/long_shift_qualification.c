#include "control.h"
#include "../system/system_internal.h"

/* $F1DD..$F20C. Carry set rejects the observation. X supplies the
 * calibration page. Two bits of the same status byte are sampled separately. */
PcmStatus pcm_long_shift_qualification(Pcm *pcm, uint16_t page, bool *admitted)
{
    uint8_t flags, sample, limit;
    if (pcm == NULL || admitted == NULL) return PCM_BAD_CONFIGURATION;
    *admitted = false;
    SYS_RUN(pcm_read8(pcm, 0x1b, &flags));
    if (flags & 0x40u) return PCM_OK;
    SYS_RUN(pcm_read8(pcm, 0x1b, &flags));
    if (flags & 0x20u) return PCM_OK;
    SYS_RUN(pcm_read8(pcm, 0xb5, &sample));
    SYS_RUN(pcm_read8(pcm, (uint16_t)(page + 0xc1u), &limit));
    if (sample < limit) return PCM_OK;
    SYS_RUN(pcm_read8(pcm, 0x16, &flags));
    if (flags & 1u) return PCM_OK;
    SYS_RUN(pcm_read8(pcm, 0x17, &flags));
    if (flags & 0x80u) return PCM_OK;
    SYS_RUN(pcm_read8(pcm, 0xb2, &sample));
    SYS_RUN(pcm_read8(pcm, (uint16_t)(page + 0xc2u), &limit));
    if (sample < limit) return PCM_OK;
    SYS_RUN(pcm_read8(pcm, 0x17, &flags));
    if (flags & 0x20u) return PCM_OK;
    SYS_RUN(pcm_read8(pcm, 0x1c, &flags));
    if (flags & 4u) return PCM_OK;
    SYS_RUN(pcm_read8(pcm, 0x1c, &flags));
    if (flags & 1u) return PCM_OK;
    SYS_RUN(pcm_read8(pcm, 0xd7, &sample));
    SYS_RUN(pcm_read8(pcm, (uint16_t)(page + 0xc3u), &limit));
    *admitted = sample >= limit;
    return PCM_OK;
}
