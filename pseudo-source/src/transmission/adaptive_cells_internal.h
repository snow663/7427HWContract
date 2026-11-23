#ifndef PCM_ADAPTIVE_CELLS_INTERNAL_H
#define PCM_ADAPTIVE_CELLS_INTERNAL_H
#include "control.h"
#include "../system/system_internal.h"

static inline PcmStatus adaptive_increment(Pcm *pcm, uint16_t address)
{
    uint8_t value;
    SYS_RUN(pcm_read8(pcm, address, &value));
    return pcm_write8(pcm, address, (uint8_t)(value + 1u));
}

/* B99F and B9EE share the bank layout and byte checksum. Service mode
 * publishes the request bits in adaptive_flags at 011A. The stock loop
 * reads its bank/cell counters from RAM at each iteration. */
static inline PcmStatus adaptive_cells(Pcm *pcm, bool restore)
{
    if (pcm == NULL) return PCM_BAD_CONFIGURATION;
    uint8_t request = restore ? 0x80u : 0x40u;
    uint8_t flags = pcm->transmission.adaptive_flags;
    if (!(flags & request)) return PCM_OK;
    pcm->transmission.adaptive_flags = (uint8_t)(flags & (uint8_t)~request);
    SYS_RUN(pcm_write8(pcm, 0x14a, 0));
    for (;;) {
        uint8_t bank, cell;
        uint16_t dest, source = 0;
        SYS_RUN(pcm_read8(pcm, 0x14a, &bank));
        if (bank == 3u) return PCM_OK;
        uint8_t offset = (uint8_t)(bank * 2u);
        SYS_RUN(pcm_read16(pcm, (uint16_t)(0xbc65u + offset), &dest));
        if (restore) SYS_RUN(pcm_read16(pcm, (uint16_t)(0xba32u + offset), &source));
        SYS_RUN(pcm_write8(pcm, 0x14b, 0));
        for (;;) {
            SYS_RUN(pcm_read8(pcm, 0x14b, &cell));
            if (cell >= 17u) break;
            uint8_t checksum, old, value = 0x80;
            SYS_RUN(pcm_read8(pcm, 0x32b, &checksum));
            SYS_RUN(pcm_serial_memory_read8(pcm, dest, &old));
            if (restore) SYS_RUN(pcm_serial_memory_read8(pcm, source++, &value));
            SYS_RUN(pcm_mask_irq(pcm, true));
            SYS_RUN(pcm_serial_memory_write8(pcm, dest++, value));
            SYS_RUN(pcm_write8(pcm, 0x32b, (uint8_t)(checksum + old - value)));
            SYS_RUN(pcm_mask_irq(pcm, false));
            SYS_RUN(adaptive_increment(pcm, 0x14b));
        }
        SYS_RUN(adaptive_increment(pcm, 0x14a));
    }
}
#endif
