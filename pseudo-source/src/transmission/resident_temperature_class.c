#include "resident_input_private_1.h"

/* B2ED..B318: signed high-byte comparison and the -1/+17
 * hysteresis. The old class is sampled again on the falling path. */
PcmStatus pcm_resident_temperature_class(Pcm *pcm)
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
