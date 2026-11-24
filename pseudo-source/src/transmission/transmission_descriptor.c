#include "gear_internal.h"

/* D8FE..D92D. On a stopped search X is the cursor. On selection X is
 * the word at the cursor, including zero. D8A7 consumes X on both exits. */
PcmStatus pcm_transmission_descriptor(Pcm *pcm, uint16_t table, uint8_t selector,
                                      uint8_t gear, uint16_t *address, bool *valid)
{
    if (pcm == NULL || address == NULL || valid == NULL) return PCM_BAD_CONFIGURATION;
    uint8_t stop_mask, stride;
    SYS_RUN(pcm_read8(pcm, table, &stop_mask));
    SYS_RUN(pcm_read8(pcm, (uint16_t)(table + 1u), &stride));
    /* D906 ASLB wraps before ABX. The two INX operations follow. */
    uint16_t cursor = (uint16_t)(table + (uint8_t)(2u * gear) + 2u);
    for (unsigned bit = 1u; ; bit <<= 1) {
        if (selector & bit) {
            uint16_t pointer;
            SYS_RUN(pcm_read16(pcm, cursor, &pointer));
            *address = pointer;
            *valid = pointer != 0;
            return PCM_OK;
        }
        if ((stop_mask & bit) || bit == 0x80u) {
            *address = cursor;
            *valid = false;
            return PCM_OK;
        }
        cursor = (uint16_t)(cursor + stride);
    }
}
