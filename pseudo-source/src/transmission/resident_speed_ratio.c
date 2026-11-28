#include "resident_input_private_1.h"

/* B2C9..B2EC. XGDX is taken if the shifted numerator vanishes; FDIV
 * produces FFFF on zero divisor or fractional quotient overflow. */
PcmStatus pcm_resident_speed_ratio(Pcm *pcm)
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
