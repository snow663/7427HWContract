#include "control.h"
#include "../system/system_internal.h"

/* $BEBC..$BEE8. Capture both throttle samples in one word read before
 * publishing B3. A negative delta is compared as its wrapped byte. */
static PcmStatus throttle_events(Pcm *pcm)
{
    uint8_t age, limit;
    SYS_RUN(pcm_read8(pcm, 0x18e, &age));
    if (age) SYS_RUN(pcm_write8(pcm, 0x18e, age - 1u));
    uint16_t samples;
    SYS_RUN(pcm_read16(pcm, 0xb2, &samples));
    uint8_t current = samples >> 8, previous = (uint8_t)samples;
    SYS_RUN(pcm_write8(pcm, 0xb3, current));
    uint8_t delta = (uint8_t)(current - previous);
    if (current < previous) {
        SYS_RUN(pcm_read8(pcm, 0x6ace, &limit));
        if (delta <= limit) {
            SYS_RUN(pcm_read8(pcm, 0x6ad1, &age));
            return pcm_write8(pcm, 0x18d, age);
        }
    } else {
        SYS_RUN(pcm_read8(pcm, 0x6acf, &limit));
        if (delta >= limit) {
            SYS_RUN(pcm_read8(pcm, 0x6ad0, &age));
            SYS_RUN(pcm_write8(pcm, 0x18e, age));
        }
    }
    SYS_RUN(pcm_read8(pcm, 0x18d, &age));
    if (age) SYS_RUN(pcm_write8(pcm, 0x18d, age - 1u));
    return PCM_OK;
}

static int32_t signed_word(uint16_t value)
{
    return value < 0x8000u ? (int32_t)value : (int32_t)value - 65536;
}

static PcmStatus throttle_limit(Pcm *pcm, uint16_t table, uint8_t *limit)
{
    uint8_t flags;
    SYS_RUN(pcm_read8(pcm, table, limit));
    SYS_RUN(pcm_read8(pcm, 0x89, &flags));
    if (flags & 0x40u) return PCM_OK;
    SYS_RUN(pcm_read8(pcm, 0x89, &flags));
    if (!(flags & 0x10u)) SYS_RUN(pcm_read8(pcm, table + 1u, limit));
    return PCM_OK;
}

PcmStatus pcm_tcc_throttle_events(Pcm *pcm)
{
    SYS_RUN(throttle_events(pcm));
    uint16_t slip, bound;
    SYS_RUN(pcm_read16(pcm, 0xeb, &slip));
    SYS_RUN(pcm_read16(pcm, 0x6ac4, &bound));
    if (signed_word(slip) < signed_word(bound))
        SYS_RUN(pcm_update8(pcm, 0x89, 0, 0x80));
    else {
        SYS_RUN(pcm_read16(pcm, 0x6ac6, &bound));
        if (signed_word(slip) > signed_word(bound)) SYS_RUN(pcm_update8(pcm, 0x89, 0x80, 0));
    }
    uint8_t limit, speed_gate, flags, sample;
    SYS_RUN(throttle_limit(pcm, 0x6aca, &limit));
    SYS_RUN(pcm_read8(pcm, 0x6ac8, &speed_gate));
    SYS_RUN(pcm_read8(pcm, 0x89, &flags));
    if (flags & 8u) SYS_RUN(pcm_read8(pcm, 0x6ac9, &speed_gate));
    SYS_RUN(pcm_update8(pcm, 0x89, 8, 0));
    SYS_RUN(pcm_read8(pcm, 0xd7, &sample));
    if (speed_gate <= sample) {
        SYS_RUN(throttle_limit(pcm, 0x6acc, &limit));
        SYS_RUN(pcm_update8(pcm, 0x89, 0, 8));
    }
    SYS_RUN(pcm_read8(pcm, 0x6ab4, &flags));
    if (!(flags & 4u)) return PCM_OK;
    SYS_RUN(pcm_read8(pcm, 0xb2, &sample));
    if (limit <= sample) return PCM_OK;
    SYS_RUN(pcm_update8(pcm, 0x8b, 0, 8));
    SYS_RUN(pcm_read8(pcm, 0x89, &flags));
    if (!(flags & 0x40u)) {
        SYS_RUN(pcm_read8(pcm, 0x8b, &flags));
        if (!(flags & 0x20u)) return PCM_OK;
    }
    SYS_RUN(pcm_read8(pcm, 0x8b, &flags));
    if (!(flags & 0x10u)) return PCM_OK;
    SYS_RUN(pcm_update8(pcm, 0x8b, 0, 0x80));
    SYS_RUN(pcm_update8(pcm, 0x8b, 0x10, 0));
    SYS_RUN(pcm_read16(pcm, 0x11b, &slip));
    SYS_RUN(pcm_read16(pcm, 0x6ae3, &bound));
    if (slip <= bound) {
        SYS_RUN(pcm_read16(pcm, 0x121, &slip));
        SYS_RUN(pcm_read16(pcm, 0x6ae7, &bound));
        uint32_t sum = (uint32_t)slip + bound;
        SYS_RUN(pcm_write16(pcm, 0x121, sum > UINT16_MAX ? UINT16_MAX : (uint16_t)sum));
    }
    return pcm_write16(pcm, 0x11b, 0);
}
