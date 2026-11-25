#include "control.h"
#include "../system/system_internal.h"

static uint8_t saturated_add(uint8_t a, uint8_t b)
{
    uint8_t sum = (uint8_t)(a + b);
    if ((uint8_t)~(a ^ b) & (a ^ sum) & 0x80u)
        return (a & 0x80u) ? 128u : 127u;
    return sum;
}

/* $B88D..$B91C. Preserve the upshift latch until the observed shift ends.
 * The FDIV divisor is the live $0844 byte, including its zero case. */
PcmStatus pcm_pressure_modifiers(Pcm *pcm, uint8_t pressure, uint8_t *result)
{
    if (pcm == NULL || result == NULL) return PCM_BAD_CONFIGURATION;
    uint8_t flags, gear, value, gain;
    SYS_RUN(pcm_read8(pcm, 0x83, &flags));
    if (flags & 2u) {
        SYS_RUN(pcm_read8(pcm, 0x84, &flags));
        if (flags & 2u) {
            SYS_RUN(pcm_update8(pcm, 0x85, 0, 0x40));
            goto check_latch;
        }
    }
    SYS_RUN(pcm_read8(pcm, 0x83, &flags));
    if (!(flags & 2u)) SYS_RUN(pcm_update8(pcm, 0x85, 0x40, 0));
check_latch:
    SYS_RUN(pcm_read8(pcm, 0x83, &flags));
    if (!(flags & 2u)) goto rpm_adjust;
    SYS_RUN(pcm_read8(pcm, 0x85, &flags));
    if (!(flags & 0x40u)) goto rpm_adjust;
    SYS_RUN(pcm_read8(pcm, 0x87, &flags));
    if (flags & 4u) {
        SYS_RUN(pcm_read8(pcm, 0xd9, &gear));
        uint8_t index = (uint8_t)(gear - 1u);
        if (!(index & 128u)) {
            SYS_RUN(pcm_read8(pcm, 0x5f16u + index, &value));
            pressure = saturated_add(pressure, value);
        }
    }
rpm_adjust:
    SYS_RUN(pcm_read8(pcm, 0x9c, &flags));
    if (flags & 4u) {
        SYS_RUN(pcm_read8(pcm, 0x1ac, &value));
        SYS_RUN(sys_curve16(pcm, value, 0x5f30, &gain));
        pressure = saturated_add(pressure, (uint8_t)(gain - 128u));
    }
    if (pressure & 128u) pressure = 0;
    SYS_RUN(pcm_read8(pcm, 0xd9, &gear));
    if (gear != 3u) {
        uint8_t divisor, numerator;
        SYS_RUN(pcm_read8(pcm, 0x844, &divisor));
        SYS_RUN(pcm_read8(pcm, 0x5f0c, &numerator));
        uint8_t fraction = numerator >= divisor ? 255u : (uint8_t)(((uint16_t)numerator << 8) / divisor);
        SYS_RUN(pcm_read8(pcm, 0x20c, &value));
        uint8_t reduction = (uint8_t)(((uint16_t)fraction * value + 128u) >> 8);
        pressure = pressure < reduction ? 0 : (uint8_t)(pressure - reduction);
    }
    SYS_RUN(pcm_read8(pcm, 0x22f, &value));
    uint8_t coordinate = value < 48u ? 0 : value >= 176u ? 255u : (uint8_t)((value - 48u) * 2u);
    SYS_RUN(sys_curve16(pcm, coordinate, 0x5f41, &gain));
    int sum = (int)pressure + (int)gain - 128;
    *result = sum < 0 ? 0 : sum > 127 ? 127 : (uint8_t)sum;
    return PCM_OK;
}
