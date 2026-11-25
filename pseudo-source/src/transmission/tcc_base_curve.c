#include "control.h"
#include "../system/system_internal.h"

/* $C271..$C2D5. Preserve the extended sign byte and sampled product in
 * RAM: the original routine updates both before producing the command. */
PcmStatus pcm_tcc_base_curve(Pcm *pcm, uint16_t curve, uint16_t override_pair)
{
    uint8_t value, offset;
    SYS_RUN(pcm_read8(pcm, override_pair, &value));
    uint16_t command = (uint16_t)(value * 257u);
    if (!value) {
        uint8_t pressure, gain, base, throttle, high, sign;
        SYS_RUN(pcm_write8(pcm, 0x192, 0));
        SYS_RUN(pcm_read8(pcm, 0xe2, &pressure));
        SYS_RUN(sys_curve16(pcm, pressure >= 128u ? 255u : (uint8_t)(pressure * 2u), 0x6e2a, &gain));
        SYS_RUN(pcm_read8(pcm, curve, &base));
        SYS_RUN(pcm_write16(pcm, 0x190, (uint16_t)gain * base));
        SYS_RUN(pcm_read8(pcm, 0xb2, &throttle));
        SYS_RUN(sys_curve16(pcm, throttle, curve, &value));
        uint16_t product = (uint16_t)gain * value, prior;
        SYS_RUN(pcm_read16(pcm, 0x190, &prior));
        uint16_t difference = (uint16_t)(product - prior);
        SYS_RUN(pcm_read8(pcm, 0x192, &sign));
        SYS_RUN(pcm_write8(pcm, 0x192, (uint8_t)(2u * sign + (product < prior))));
        SYS_RUN(pcm_read8(pcm, 0x192, &sign));
        SYS_RUN(pcm_write8(pcm, 0x192, (uint8_t)(0u - sign)));
        SYS_RUN(pcm_read8(pcm, 0x192, &sign));
        SYS_RUN(pcm_write8(pcm, 0x192, (uint8_t)(2u * sign + (difference >> 15))));
        command = (uint16_t)(difference << 1);
        SYS_RUN(pcm_read8(pcm, curve, &base));
        unsigned upper = (command >> 8) + base;
        command = (uint16_t)((upper << 8) | (uint8_t)command);
        SYS_RUN(pcm_read8(pcm, 0x192, &sign));
        /* BGE uses signed N xor V after ADCB. */
        int extended = (sign < 128u ? (int)sign : (int)sign - 256) + (int)(upper >> 8);
        if (extended < 0) command = 0;
        else if (extended) command = UINT16_MAX;
        if (extended <= 0) {
            high = (uint8_t)(command >> 8);
            SYS_RUN(pcm_write8(pcm, 0x18f, high));
            SYS_RUN(pcm_read8(pcm, 0x18f, &high));
            unsigned low = (uint8_t)command + high;
            uint32_t rounded = (uint32_t)(command & 0xff00u) + low + (low >> 8);
            command = rounded > UINT16_MAX ? UINT16_MAX : (uint16_t)rounded;
        }
    }
    SYS_RUN(pcm_read8(pcm, (uint16_t)(override_pair + 1u), &offset));
    int adjusted = (int)(command >> 8) + (offset < 128u ? (int)offset : (int)offset - 256);
    if (adjusted < 0) command = 0;
    else if (adjusted > 255) command = UINT16_MAX;
    else command = (uint16_t)(((uint16_t)adjusted << 8) | (uint8_t)command);
    return pcm_write16(pcm, 0xf1, command);
}
