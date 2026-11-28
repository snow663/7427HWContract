#include "batch1.h"
#include "../src/system/system_internal.h"

/* B2B2..B2C8. The first word is sampled even when the forward table
 * supersedes it. ASLB truncates the doubled index to eight bits. */
PcmStatus closure_gear_ratio(Pcm *pcm, uint16_t *ratio)
{
    uint8_t range, gear, fault;
    SYS_RUN(pcm_read16(pcm, 0x5b43, ratio));
    SYS_RUN(pcm_read8(pcm, 0xa2, &range));
    if (range & 0x20u) return PCM_OK;
    SYS_RUN(pcm_read8(pcm, 0xd9, &gear));
    SYS_RUN(pcm_read8(pcm, 0x98, &fault));
    if (fault & 4u) gear = 1;
    return pcm_read16(pcm, (uint16_t)(0x5b49u + (uint8_t)(gear << 1)), ratio);
}

/* B2C9..B2EC. XGDX is taken if the shifted numerator vanishes; FDIV
 * produces FFFF on zero divisor or fractional quotient overflow. */
PcmStatus closure_speed_ratio(Pcm *pcm)
{
    uint8_t gear, flags;
    uint16_t numerator, denominator;
    SYS_RUN(pcm_update8(pcm, 0x9a, 2, 0));
    SYS_RUN(pcm_read8(pcm, 0xd9, &gear));
    if (gear >= 3u) {
        SYS_RUN(pcm_read8(pcm, 0x89, &flags));
        if (flags & 0x20u) {
            SYS_RUN(pcm_read16(pcm, 0x1ac, &numerator));
            SYS_RUN(pcm_read16(pcm, 0xc2, &denominator));
            goto divide;
        }
        SYS_RUN(pcm_update8(pcm, 0x9a, 0, 2));
    }
    SYS_RUN(pcm_read16(pcm, 0xc2, &numerator));
    SYS_RUN(pcm_read16(pcm, 0xd3, &denominator));
divide:
    numerator >>= 2;
    if (!numerator) {
        numerator = denominator;
        denominator = 0;
    }
    uint16_t result = UINT16_MAX;
    if (denominator && numerator < denominator)
        result = (uint16_t)(((uint32_t)numerator << 16) / denominator);
    return pcm_write16(pcm, 0xf9, result);
}

static int16_t signed_byte(uint8_t x)
{
    return x < 128u ? (int16_t)x : (int16_t)x - 256;
}

/* B2ED..B318: signed high-byte comparison and the -1/+17
 * hysteresis. The old class is sampled again on the falling path. */
PcmStatus closure_temperature_class(Pcm *pcm)
{
    uint8_t temp, old, value;
    SYS_RUN(pcm_read8(pcm, 0xb5, &temp));
    uint16_t word = (uint16_t)((uint16_t)temp * 8u - 1u);
    if (!(word & 0x8000u)) {
        SYS_RUN(pcm_read8(pcm, 0x152, &old));
        if (signed_byte((uint8_t)(word >> 8)) >= signed_byte(old))
            goto publish;
    }
    word = (uint16_t)(word + 17u);
    SYS_RUN(pcm_read8(pcm, 0x152, &old));
    if (signed_byte((uint8_t)(word >> 8)) >= signed_byte(old))
        goto tables;
publish:
    SYS_RUN(pcm_write8(pcm, 0x152, (uint8_t)(word >> 8)));
tables:
    SYS_RUN(pcm_read8(pcm, 0x152, &old));
    SYS_RUN(pcm_read8(pcm, (uint16_t)(0xb31du + old), &value));
    SYS_RUN(pcm_write8(pcm, 0x153, value));
    SYS_RUN(pcm_read8(pcm, (uint16_t)(0xb325u + old), &value));
    return pcm_write8(pcm, 0x154, value);
}

/* The factory samples suppression, enable and live status in that order.
 * Preserve the separate reads and stop at the first nonzero witness. */
static PcmStatus mask_test(Pcm *pcm, uint16_t suppress, uint16_t enable,
                           uint16_t live, uint8_t bits, bool *active)
{
    uint8_t a, b, c;
    SYS_RUN(pcm_read8(pcm, suppress, &a));
    SYS_RUN(pcm_read8(pcm, enable, &b));
    SYS_RUN(pcm_read8(pcm, live, &c));
    *active = (((uint8_t)~a & b & c & bits) != 0);
    return PCM_OK;
}

/* E5CF..E5F0 */
PcmStatus closure_fault_e5cf(Pcm *pcm)
{
    bool active;
    SYS_RUN(mask_test(pcm, 0x5b34, 0x5b2b, 0x16, 1, &active));
    if (!active) SYS_RUN(mask_test(pcm, 0x5b35, 0x5b2c, 0x17, 0x80, &active));
    return pcm_update8(pcm, 0x98, 1, active ? 1 : 0);
}

/* E5F1..E60A */
PcmStatus closure_fault_e5f1(Pcm *pcm)
{
    uint8_t a, b;
    SYS_RUN(pcm_read8(pcm, 0x5b2f, &a));
    SYS_RUN(pcm_read8(pcm, 0x1a, &b));
    bool active = (a & b & 0x18u) != 0;
    if (!active) {
        SYS_RUN(pcm_read8(pcm, 0x86, &a));
        if (!(a & 0x80u)) {
            SYS_RUN(pcm_read8(pcm, 0x100, &b));
            active = b == 0;
        }
    }
    return pcm_update8(pcm, 0x99, 8, active ? 8 : 0);
}

/* E60B..E62C and E6F5..E716 share the exact mask-scan form. */
static PcmStatus paired_fault(Pcm *pcm, uint8_t first, uint8_t second, uint8_t bit)
{
    bool active;
    SYS_RUN(mask_test(pcm, 0x5b35, 0x5b2c, 0x17, first, &active));
    if (!active) SYS_RUN(mask_test(pcm, 0x5b3a, 0x5b31, 0x1c, second, &active));
    return pcm_update8(pcm, 0x98, bit, active ? bit : 0);
}
PcmStatus closure_fault_e60b(Pcm *pcm) { return paired_fault(pcm, 0x20, 4, 2); }
PcmStatus closure_fault_e6f5(Pcm *pcm) { return paired_fault(pcm, 2, 0x20, 4); }
