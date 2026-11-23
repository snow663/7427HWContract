#include "slot_d_internal.h"

/* E228..E257. The cursor counts bits across nine history bytes, MSB first. */
static PcmStatus next_code(Pcm *pcm, bool *found)
{
    uint8_t cursor, bits, enabled;
    for (;;) {
        D_READ(0x0216, cursor);
        if (cursor > 71u) {
            D_STORE(0x0216, 0);
            D_CLEAR(0x3c, 0x40);
            *found = false;
            return PCM_OK;
        }
        if (!(cursor & 7u)) {
            D_READ((uint16_t)(0x0b + (cursor >> 3)), bits);
            D_READ((uint16_t)(0x5b00 + (cursor >> 3)), enabled);
            D_STORE(0x0217, (uint8_t)(bits & enabled));
        }
        D_COUNT(0x0216, 1, cursor);
        D_READ(0x0217, bits);
        D_STORE(0x0217, (uint8_t)(bits << 1));
        if (bits & 0x80u) {
            *found = true;
            return PCM_OK;
        }
    }
}

/* E1EC..E285. Code 12 is the first (cursor zero) packed digit pair.
 * Decoding and flashing only change the logical lamp request. */
PcmStatus pcm_diagnostic_flash_codes(Pcm *pcm)
{
    if (pcm == NULL) return PCM_BAD_CONFIGURATION;
    uint8_t flags, counter, cursor, packed, delay = 28;
    D_READ(0x3c, flags);
    if (!(flags & 0x40u)) goto start;
    D_COUNT(0x0218, -1, counter);
    if (counter) goto publish;
    D_READ(0x71, flags);
    if (flags & 1u) {
        delay = 4;
        goto gap;
    }
    D_READ(0x3c, flags);
    uint16_t digit = flags & 0x20u ? 0x0215 : 0x0214;
    D_COUNT(digit, -1, counter);
    if (!(counter & 0x80u)) {
        D_SET(0x71, 1);
        D_STORE(0x0218, 4);
        goto publish;
    }
    D_READ(0x3c, flags);
    if (!(flags & 0x20u)) {
        D_SET(0x3c, 0x20);
        delay = 8;
        goto gap;
    }
    D_CLEAR(0x3c, 0x20);
    D_READ(0x3c, flags);
    if (flags & 3u) {
        D_COUNT(0x3c, -1, counter);
        goto digits;
    }
    bool found;
    SYS_RUN(next_code(pcm, &found));
    if (!found) goto lamp_off;
start:
    D_SET(0x3c, 2);
digits:
    D_READ(0x0216, cursor);
    D_READ((uint16_t)(0xfe56u + cursor), packed);
    SYS_RUN(pcm_write16(pcm, 0x0214, (uint16_t)((uint16_t)(packed >> 4) * 256u + (packed & 15u))));
    D_SET(0x3c, 0x40);
gap:
    D_STORE(0x0218, delay);
lamp_off:
    D_CLEAR(0x71, 1);
publish:
    D_READ(0x71, flags);
    return d_update(pcm, 0x72, 0x80, flags & 1u ? 0x80 : 0);
}
