#include "spark_internal.h"

/* $DBC2..$DBDF. IDIV returns FFFF on zero divisor. The direction
 * flag selects the endpoint whenever the quotient exceeds one byte. */
static PcmStatus publish_fraction(Pcm *pcm, uint8_t distance, uint8_t span)
{
    uint16_t quotient = span ? (uint16_t)(((uint16_t)distance << 8) / span) : UINT16_MAX;
    uint8_t peak = 0;
    if (quotient <= 255u) {
        SYS_RUN(pcm_read8(pcm, 0x15b, &peak));
        peak = (uint8_t)(((uint16_t)peak * quotient + 128u) >> 8);
    } else if (!(pcm->spark.transmission_status & 0x80u)) {
        SYS_RUN(pcm_read8(pcm, 0x15b, &peak));
    }
    pcm->spark.transmission_retard = peak;
    return PCM_OK;
}

static PcmStatus end_shift(Pcm *pcm)
{
    pcm->spark.transmission_status &= (uint8_t)~8u;
    pcm->spark.transmission_retard = 0;
    return PCM_OK;
}

/* $DB3B..$DB82. Each indirect knot goes through its ROM pointer. */
static PcmStatus ratio_shape(Pcm *pcm, uint8_t gear)
{
    uint16_t pointers = (uint16_t)(0xdbeb + 2u * (gear - 1u)), knot;
    uint8_t ratio, first, second;
    SYS_RUN(pcm_read16(pcm, pointers + 4u, &knot));
    SYS_RUN(pcm_read8(pcm, 0xf9, &ratio));
    SYS_RUN(pcm_read8(pcm, knot, &second));
    if (ratio > second) {
        pcm->spark.transmission_status |= 0x80u;
        SYS_RUN(pcm_read16(pcm, pointers, &knot));
        SYS_RUN(pcm_read8(pcm, knot, &first));
        SYS_RUN(pcm_read16(pcm, pointers + 4u, &knot));
        SYS_RUN(pcm_read8(pcm, knot, &second));
        SYS_RUN(pcm_read8(pcm, 0xf9, &ratio));
        if (first < ratio) {
            pcm->spark.transmission_retard = 0;
            return PCM_OK;
        }
        return publish_fraction(pcm, (uint8_t)(first - ratio), (uint8_t)(first - second));
    }
    SYS_RUN(pcm_read16(pcm, pointers + 12u, &knot));
    SYS_RUN(pcm_read8(pcm, knot, &second));
    if (ratio <= second) return end_shift(pcm);
    SYS_RUN(pcm_read16(pcm, pointers + 8u, &knot));
    SYS_RUN(pcm_read8(pcm, knot, &first));
    SYS_RUN(pcm_read16(pcm, pointers + 12u, &knot));
    SYS_RUN(pcm_read8(pcm, knot, &second));
    uint8_t span = (uint8_t)(first - second);
    SYS_RUN(pcm_read8(pcm, 0xf9, &ratio));
    SYS_RUN(pcm_read8(pcm, knot, &second));
    return publish_fraction(pcm, (uint8_t)(ratio - second), span);
}

static PcmStatus age_shape(Pcm *pcm)
{
    uint8_t age, upper, lower;
    SYS_RUN(pcm_read8(pcm, 0x15c, &age));
    age = (uint8_t)(age + 1u);
    if (!age) return end_shift(pcm);
    SYS_RUN(pcm_write8(pcm, 0x15c, age));
    SYS_RUN(pcm_read8(pcm, 0x70cf, &upper));
    uint8_t distance, span;
    if (age < upper) {
        pcm->spark.transmission_status |= 0x80u;
        SYS_RUN(pcm_read8(pcm, 0x70cf, &upper));
        SYS_RUN(pcm_read8(pcm, 0x70ce, &lower));
        span = (uint8_t)(upper - lower);
        SYS_RUN(pcm_read8(pcm, 0x15c, &age));
        SYS_RUN(pcm_read8(pcm, 0x70ce, &lower));
        if (age < lower) goto zero;
        distance = (uint8_t)(age - lower);
    } else {
        SYS_RUN(pcm_read8(pcm, 0x70d1, &upper));
        if (age >= upper) return end_shift(pcm);
        SYS_RUN(pcm_read8(pcm, 0x70d1, &upper));
        SYS_RUN(pcm_read8(pcm, 0x70d0, &lower));
        span = (uint8_t)(upper - lower);
        SYS_RUN(pcm_read8(pcm, 0x70d1, &upper));
        SYS_RUN(pcm_read8(pcm, 0x15c, &age));
        if (upper < age) goto zero;
        distance = (uint8_t)(upper - age);
    }
    return publish_fraction(pcm, distance, span);
zero:
    pcm->spark.transmission_retard = 0;
    return PCM_OK;
}

/* $DAE2..$DBE2. Range retard has priority, even over clearing shift state. */
PcmStatus pcm_transmission_shift_retard(Pcm *pcm)
{
    if (pcm->spark.transmission_status & 0x17u) return PCM_OK;
    uint8_t range, events;
    SYS_RUN(pcm_read8(pcm, 0xa2, &range));
    if ((range & 0x70u) || (pcm->transmission.inhibit_flags & 0x10u)) return end_shift(pcm);
    pcm->spark.transmission_status &= (uint8_t)~0x80u;
    SYS_RUN(pcm_read8(pcm, 0x83, &events));
    if (events & 1u) {
        pcm->spark.transmission_status |= 8u;
        SYS_RUN(pcm_write8(pcm, 0x15b, 0));
        SYS_RUN(pcm_write8(pcm, 0x15c, 0));
    }
    if (!(pcm->spark.transmission_status & 8u)) return end_shift(pcm);
    SYS_RUN(pcm_read8(pcm, 0x83, &events));
    if (events & 8u) return end_shift(pcm);
    uint8_t gear = pcm->transmission.selected_gear;
    uint16_t table;
    SYS_RUN(pcm_read16(pcm, (uint16_t)(0xdbe3u + (uint8_t)(gear << 1)), &table));
    uint8_t value, peak;
    SYS_RUN(transmission_retard_surface(pcm, table, &value));
    SYS_RUN(pcm_read8(pcm, 0x15b, &peak));
    if (value >= peak) SYS_RUN(pcm_write8(pcm, 0x15b, value));
    gear = pcm->transmission.selected_gear;
    if (gear == 1u || gear == 2u) return ratio_shape(pcm, gear);
    return age_shape(pcm);
}
