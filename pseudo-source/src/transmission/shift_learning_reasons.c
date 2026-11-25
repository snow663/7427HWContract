#include "control.h"
#include "../system/system_internal.h"

/* $B4B2..$B56A. $90 and $91 accumulate reasons. Only $92 is rebuilt.
 * The per-gear index is an unsigned wrapped DECB followed by ABX. */
PcmStatus pcm_shift_learning_reasons(Pcm *pcm)
{
    uint8_t reasons, flags, value, limit, throttle, gear;
    SYS_RUN(pcm_read8(pcm, 0x90, &reasons));
    SYS_RUN(pcm_read8(pcm, 0xd9, &gear));
    uint16_t table = (uint16_t)(0x68b8u + (uint8_t)(gear - 1u));
    SYS_RUN(pcm_read8(pcm, 0x8e, &flags));
    if (flags & 4u) reasons |= 8u;
    SYS_RUN(pcm_read8(pcm, 0x68a8, &flags));
    if (flags & 1u) {
        SYS_RUN(pcm_read8(pcm, 0xda, &value));
        SYS_RUN(pcm_read8(pcm, table + 0xefu, &limit));
        if (value > limit) SYS_RUN(pcm_update8(pcm, 0x91, 0, 0x80));
    }
    SYS_RUN(pcm_read8(pcm, 0xdc, &value));
    SYS_RUN(pcm_read8(pcm, table + 0x16u, &limit));
    if (value > limit) reasons |= 0x20u;
    SYS_RUN(pcm_read8(pcm, 0xb2, &throttle));
    SYS_RUN(pcm_read8(pcm, table + 3u, &limit));
    if (throttle > limit) {
        SYS_RUN(pcm_read8(pcm, table + 6u, &limit));
        if (throttle > limit) reasons |= 4u;
    } else reasons |= 4u;

    SYS_RUN(pcm_read8(pcm, 0x195, &value));
    uint8_t difference = throttle >= value ? throttle - value : value - throttle;
    SYS_RUN(pcm_read8(pcm, 0x68c1, &limit));
    if (difference >= limit) reasons |= 0x80u;
    SYS_RUN(pcm_read8(pcm, 0x9f, &flags));
    if (flags & 4u) reasons |= 1u;
    else {
        SYS_RUN(pcm_read8(pcm, 0x68a8, &flags));
        if (flags & 4u) {
            SYS_RUN(pcm_read8(pcm, 0x9f, &flags));
            if (flags & 2u) reasons |= 1u;
        }
    }
    SYS_RUN(pcm_read8(pcm, 0xb5, &value));
    SYS_RUN(pcm_read8(pcm, 0x68b9, &limit));
    if (value > limit) {
        SYS_RUN(pcm_read8(pcm, 0x68ba, &limit));
        if (value >= limit) reasons |= 2u;
    } else reasons |= 2u;
    SYS_RUN(pcm_read8(pcm, 0xa2, &flags));
    if (flags & 3u) reasons |= 0x10u;
    SYS_RUN(pcm_read8(pcm, 0x68b8, &limit));
    SYS_RUN(pcm_read8(pcm, 0xdb, &value));
    if (limit == value) {
        SYS_RUN(pcm_read8(pcm, 0xda, &value));
        if (limit > value) reasons |= 0x40u;
    }
    SYS_RUN(pcm_write8(pcm, 0x90, reasons));
    SYS_RUN(pcm_transmission_fault_gate_654(pcm));

    SYS_RUN(pcm_read8(pcm, 0x91, &reasons));
    SYS_RUN(pcm_read8(pcm, 0x98, &flags));
    if (flags & 0x10u) reasons |= 8u;
    SYS_RUN(pcm_read8(pcm, 0xd9, &gear));
    table = (uint16_t)(0x68b8u + (uint8_t)(gear - 1u));
    SYS_RUN(pcm_read8(pcm, 0x188, &value));
    SYS_RUN(pcm_read8(pcm, table + 10u, &limit));
    if (value < limit) reasons |= 1u;
    SYS_RUN(pcm_read8(pcm, 0xa1, &value));
    SYS_RUN(pcm_read8(pcm, table + 13u, &limit));
    if (value < limit) reasons |= 2u;
    SYS_RUN(pcm_read8(pcm, 0xd7, &value));
    SYS_RUN(pcm_read8(pcm, 0x187, &limit));
    /* BPL tests the sign of the wrapped byte at $B550. */
    difference = (uint8_t)(value - limit);
    if (difference & 0x80u) difference = (uint8_t)(0u - difference);
    SYS_RUN(pcm_read8(pcm, table + 16u, &limit));
    if (difference > limit) reasons |= 4u;
    SYS_RUN(pcm_write8(pcm, 0x91, reasons));

    SYS_RUN(pcm_read8(pcm, 0x9c, &flags));
    reasons = (flags & 0x20u) ? 1u : 0u;
    SYS_RUN(pcm_read8(pcm, 0x87, &flags));
    if (flags & 2u) reasons |= 2u;
    return pcm_write8(pcm, 0x92, reasons);
}
