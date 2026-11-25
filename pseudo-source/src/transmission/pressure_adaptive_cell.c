#include "control.h"
#include "../system/system_internal.h"

/* $B91D..$B960. An upshift already under observation may retain its
 * previous correction. The return reloads $0148 even on the retained path. */
PcmStatus pcm_pressure_adaptive_cell(Pcm *pcm, uint8_t *correction)
{
    if (pcm == NULL || correction == NULL) return PCM_BAD_CONFIGURATION;
    uint8_t gear, flags, sample, value = 0;
    SYS_RUN(pcm_read8(pcm, 0xd9, &gear));
    SYS_RUN(pcm_read8(pcm, 0x83, &flags));
    if (flags & 2u) {
        SYS_RUN(pcm_read8(pcm, 0x83, &flags));
        if (!(flags & 1u)) {
            uint8_t reasons, other;
            SYS_RUN(pcm_read8(pcm, 0x90, &reasons));
            SYS_RUN(pcm_read8(pcm, 0x91, &other));
            reasons |= other;
            SYS_RUN(pcm_read8(pcm, 0x92, &other));
            if (!(reasons | other)) goto result;
        }
    } else {
        SYS_RUN(pcm_read8(pcm, 0x83, &flags));
        if (flags & 0x10u) gear = (uint8_t)(gear + 1u);
    }
    uint8_t index = (uint8_t)(gear - 1u);
    uint16_t table = 0;
    if (!(index & 0x80u))
        SYS_RUN(pcm_read16(pcm, 0xbc65u + (uint8_t)(index << 1), &table));
    if (table) {
        SYS_RUN(pcm_read8(pcm, 0xb2, &sample));
        SYS_RUN(pcm_write8(pcm, 0x149, (uint8_t)((sample + 8u) >> 4)));
        SYS_RUN(pcm_read8(pcm, 0xb2, &sample));
        SYS_RUN(sys_curve16(pcm, sample, table, &value));
        value = (uint8_t)(value - 128u);
    } else SYS_RUN(pcm_write8(pcm, 0x149, 0));
    SYS_RUN(pcm_write8(pcm, 0x148, value));
result:
    return pcm_read8(pcm, 0x148, correction);
}
