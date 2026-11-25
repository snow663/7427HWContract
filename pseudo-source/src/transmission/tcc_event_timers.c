#include "control.h"
#include "../system/system_internal.h"

static PcmStatus age_byte(Pcm *pcm, uint16_t address)
{
    uint8_t age;
    SYS_RUN(pcm_read8(pcm, address, &age));
    if (age != 255u) SYS_RUN(pcm_write8(pcm, address, age + 1u));
    return PCM_OK;
}

static PcmStatus shift_delay(Pcm *pcm, uint16_t timer, uint8_t event, uint16_t table)
{
    uint8_t delay, flags, gear;
    SYS_RUN(pcm_read8(pcm, timer, &delay));
    if (delay) --delay;
    else {
        SYS_RUN(pcm_read8(pcm, 0x83, &flags));
        if (!(flags & event)) return PCM_OK;
        SYS_RUN(pcm_read8(pcm, 0xd9, &gear));
        uint8_t index = event == 1u ? (uint8_t)(gear - 1u) : gear;
        SYS_RUN(pcm_read8(pcm, table + index, &delay));
    }
    return pcm_write8(pcm, timer, delay);
}

/* $BF62..$C00A. The two word counters saturate with different store
 * behavior. The accumulator decays before enforcing the calibrated floor. */
PcmStatus pcm_tcc_event_timers(Pcm *pcm)
{
    uint16_t age, limit, accumulated;
    SYS_RUN(pcm_read16(pcm, 0x11b, &age));
    if (age != UINT16_MAX) SYS_RUN(pcm_write16(pcm, 0x11b, age + 1u));
    SYS_RUN(pcm_read16(pcm, 0x11d, &age));
    if (age != UINT16_MAX) ++age;
    SYS_RUN(pcm_write16(pcm, 0x11d, age));
    SYS_RUN(pcm_read16(pcm, 0x6ae5, &limit));
    if (age >= limit) {
        SYS_RUN(pcm_write16(pcm, 0x11d, 0));
        SYS_RUN(pcm_read16(pcm, 0x121, &accumulated));
        SYS_RUN(pcm_read16(pcm, 0x6ae9, &limit));
        accumulated = accumulated < limit ? 0 : accumulated - limit;
        SYS_RUN(pcm_write16(pcm, 0x121, accumulated));
    }
    SYS_RUN(pcm_read16(pcm, 0x121, &accumulated));
    SYS_RUN(pcm_read16(pcm, 0x6ae1, &limit));
    if (accumulated < limit) {
        SYS_RUN(pcm_read16(pcm, 0x6ae1, &limit));
        SYS_RUN(pcm_write16(pcm, 0x121, limit));
    }
    uint8_t flags, delay, maximum;
    SYS_RUN(pcm_read8(pcm, 0x8b, &flags));
    if (flags & 0x20u) {
        SYS_RUN(pcm_read8(pcm, 0x123, &delay));
        SYS_RUN(pcm_read8(pcm, 0x6aeb, &maximum));
        if (delay < maximum) {
            SYS_RUN(pcm_write8(pcm, 0x123, delay + 1u));
            goto age_timers;
        }
        SYS_RUN(pcm_update8(pcm, 0x8b, 0x20, 0));
    }
    SYS_RUN(pcm_write8(pcm, 0x123, 0));
age_timers:
    SYS_RUN(age_byte(pcm, 0x12d));
    SYS_RUN(age_byte(pcm, 0x12e));
    SYS_RUN(pcm_read8(pcm, 0x89, &flags));
    if (!(flags & 0x40u)) {
        SYS_RUN(pcm_read8(pcm, 0x89, &flags));
        if (!(flags & 0x10u)) SYS_RUN(age_byte(pcm, 0x125));
    }
    SYS_RUN(shift_delay(pcm, 0x18c, 8, 0x6ad2));
    return shift_delay(pcm, 0x124, 1, 0x6ad5);
}
