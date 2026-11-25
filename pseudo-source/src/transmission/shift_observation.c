#include "control.h"
#include "../system/system_internal.h"

/* $B378..$B3DF. Paired event bits cancel an older observation before
 * a fresh edge can arm and initialize the next one. */
static PcmStatus admit_shift(Pcm *pcm)
{
    uint8_t events, flags, value, previous;
    SYS_RUN(pcm_read8(pcm, 0x83, &events));
    bool cancel = (events & 0x11u) == 0x11u;
    if (!cancel) {
        SYS_RUN(pcm_read8(pcm, 0x83, &events));
        cancel = (events & 0x0au) == 0x0au;
    }
    if (cancel) {
        SYS_RUN(pcm_update8(pcm, 0x83, 0x12, 0));
        SYS_RUN(pcm_update8(pcm, 0x85, 2, 0));
    }
    SYS_RUN(pcm_read8(pcm, 0x85, &flags));
    if (!(flags & 2u)) {
        SYS_RUN(pcm_read8(pcm, 0x83, &events));
        if (!(events & 9u)) return PCM_OK;
        SYS_RUN(pcm_update8(pcm, 0x85, 0, 2));
        SYS_RUN(pcm_update8(pcm, 0x85, 0x10, 0));
        SYS_RUN(pcm_update8(pcm, 0x85, 0x80, 0));
        SYS_RUN(pcm_update8(pcm, 0x83, 0x12, 0));
        SYS_RUN(pcm_read8(pcm, 0x83, &events));
        if (events & 1u) SYS_RUN(pcm_update8(pcm, 0x83, 0, 2));
        SYS_RUN(pcm_read8(pcm, 0x83, &events));
        if (events & 8u) SYS_RUN(pcm_update8(pcm, 0x83, 0, 0x10));
        SYS_RUN(pcm_update8(pcm, 0x8e, 8, 0));
        SYS_RUN(pcm_read8(pcm, 0xa1, &value));
        if (!value) SYS_RUN(pcm_update8(pcm, 0x8e, 0, 8));
        SYS_RUN(pcm_read8(pcm, 0xdb, &value));
        SYS_RUN(pcm_write8(pcm, 0x188, value));
        SYS_RUN(pcm_write8(pcm, 0xda, 0));
        SYS_RUN(pcm_write8(pcm, 0xdb, 0));
        SYS_RUN(pcm_write16(pcm, 0x19a, 0));
        SYS_RUN(pcm_write8(pcm, 0xdf, 127));
        SYS_RUN(pcm_write8(pcm, 0xe0, 127));
        SYS_RUN(pcm_read8(pcm, 0xa0, &value));
        SYS_RUN(pcm_read8(pcm, 0x9f, &previous));
        SYS_RUN(pcm_write8(pcm, 0x90, ((value ^ previous) & 7u) != 0));
        SYS_RUN(pcm_write8(pcm, 0x91, 0));
        SYS_RUN(pcm_write8(pcm, 0x92, 0));
        SYS_RUN(pcm_read8(pcm, 0xb2, &value));
        SYS_RUN(pcm_write8(pcm, 0x195, value));
    }
    SYS_RUN(pcm_read8(pcm, 0x83, &events));
    if (events & 1u) return PCM_OK;
    SYS_RUN(pcm_read8(pcm, 0x83, &events));
    if (!(events & 8u)) SYS_RUN(pcm_update8(pcm, 0x85, 2, 0));
    return PCM_OK;
}

static PcmStatus finish_window(Pcm *pcm)
{
    uint8_t duration, gear, limit;
    uint16_t mean;
    SYS_RUN(pcm_read8(pcm, 0xdc, &duration));
    SYS_RUN(pcm_read16(pcm, 0x19a, &mean));
    if (mean != UINT16_MAX) {
        uint16_t quotient = duration ? mean / duration : UINT16_MAX;
        mean = quotient > 0x07ffu ? UINT16_MAX : (uint16_t)(quotient << 5);
        SYS_RUN(pcm_write16(pcm, 0x19a, mean));
    }
    SYS_RUN(pcm_read8(pcm, 0xd9, &gear));
    SYS_RUN(pcm_write8(pcm, 0x19cu + (uint8_t)(gear - 1u), (uint8_t)(mean >> 8)));
    SYS_RUN(pcm_read8(pcm, 0xd9, &gear));
    SYS_RUN(pcm_read8(pcm, 0xdc, &duration));
    SYS_RUN(pcm_read8(pcm, 0x68cbu + (uint8_t)(gear - 1u), &limit));
    if (duration < limit) SYS_RUN(pcm_update8(pcm, 0x91, 0, 0x40));
    SYS_RUN(pcm_shift_adaptive_learning(pcm));
    return pcm_long_shift_diagnostic(pcm);
}

/* $B367..$B4B1. Sample origin, accumulate ratio, then learn at the lower
 * crossing or timeout. The upper and lower thresholds are gear-indexed words. */
PcmStatus pcm_shift_observation(Pcm *pcm)
{
    uint8_t age, origin, gear, events, flags;
    SYS_RUN(pcm_read8(pcm, 0xdb, &age));
    if (age != 255u) SYS_RUN(pcm_write8(pcm, 0xdb, age + 1u));
    SYS_RUN(admit_shift(pcm));
    SYS_RUN(pcm_read8(pcm, 0xd9, &gear));
    SYS_RUN(pcm_read8(pcm, 0x83, &events));
    uint8_t index = (events & 0x10u) ? gear : (uint8_t)(gear - 1u);
    SYS_RUN(pcm_read8(pcm, 0x85, &flags));
    if (flags & 0x80u) return PCM_OK;
    SYS_RUN(pcm_read8(pcm, 0xdb, &age));
    SYS_RUN(pcm_read8(pcm, 0xda, &origin));
    SYS_RUN(pcm_write8(pcm, 0xdc, (uint8_t)(age - origin)));
    uint16_t table = (uint16_t)(0x68a9u + 2u*index), ratio, limit;
    SYS_RUN(pcm_read16(pcm, 0xf9, &ratio));
    SYS_RUN(pcm_read8(pcm, 0xd9, &gear));
    if (gear) {
        SYS_RUN(pcm_read8(pcm, 0x83, &events));
        if (!(events & 0x10u)) goto upshift;
    }
    SYS_RUN(pcm_read8(pcm, 0xdb, &age));
    SYS_RUN(pcm_read8(pcm, 0xd9, &gear));
    uint8_t timeout;
    SYS_RUN(pcm_read8(pcm, 0x68b5u + gear, &timeout));
    if (age < timeout) return PCM_OK;
    goto complete;
upshift:
    SYS_RUN(pcm_read8(pcm, 0x9a, &flags));
    if (flags & 2u) {
        SYS_RUN(pcm_update8(pcm, 0x91, 0, 0x10));
        SYS_RUN(pcm_update8(pcm, 0x9a, 0, 0x10));
        SYS_RUN(pcm_shift_learning_reasons(pcm));
    } else {
        SYS_RUN(pcm_read16(pcm, table, &limit));
        if (ratio >= limit) {
            SYS_RUN(pcm_write16(pcm, 0x19a, 0));
            SYS_RUN(pcm_update8(pcm, 0x85, 0x10, 0));
            SYS_RUN(pcm_read8(pcm, 0xdb, &age));
            SYS_RUN(pcm_write8(pcm, 0xda, age));
            SYS_RUN(pcm_read8(pcm, 0xd9, &gear));
            SYS_RUN(pcm_write8(pcm, 0x189u + (uint8_t)(gear - 1u), age));
        } else {
            SYS_RUN(pcm_read16(pcm, table + 6u, &limit));
            if (ratio < limit) goto finish;
            SYS_RUN(pcm_read16(pcm, 0xf9, &ratio));
            uint16_t accumulator;
            SYS_RUN(pcm_read16(pcm, 0x19a, &accumulator));
            uint32_t sum = (uint32_t)accumulator + (ratio >> 5);
            SYS_RUN(pcm_write16(pcm, 0x19a, sum > UINT16_MAX ? UINT16_MAX : (uint16_t)sum));
            SYS_RUN(pcm_update8(pcm, 0x85, 0, 0x10));
        }
        SYS_RUN(pcm_shift_learning_reasons(pcm));
        SYS_RUN(pcm_read8(pcm, 0xdb, &age));
        if (age != 255u) return PCM_OK;
    }
finish:
    SYS_RUN(finish_window(pcm));
complete:
    SYS_RUN(pcm_update8(pcm, 0x85, 0, 0x80));
    SYS_RUN(pcm_update8(pcm, 0x85, 2, 0));
    return pcm_update8(pcm, 0x83, 0x12, 0);
}
