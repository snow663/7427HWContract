#include "control.h"
#include "../system/system_internal.h"

/* $BA38..$BA5E. Count a fresh $93.5 observation once per latch cycle.
 * The table may specify a null bank. The final latch uses the captured bit. */
PcmStatus pcm_pressure_learning_count(Pcm *pcm)
{
    uint8_t flags, gear, coordinate, value;
    SYS_RUN(pcm_read8(pcm, 0x93, &flags));
    if ((flags & 0x60u) == 0x20u) {
        SYS_RUN(pcm_read8(pcm, 0xd9, &gear));
        uint16_t bank;
        uint8_t index = (uint8_t)(gear - 1u);
        SYS_RUN(pcm_read16(pcm, 0xba5fu + (uint8_t)(index << 1), &bank));
        if (bank) {
            SYS_RUN(pcm_read8(pcm, 0x149, &coordinate));
            uint16_t address = (uint16_t)(bank + coordinate);
            SYS_RUN(pcm_read8(pcm, address, &value));
            SYS_RUN(pcm_write8(pcm, address, (uint8_t)(value + 1u)));
        }
    }
    return pcm_update8(pcm, 0x93, 0x40, (flags & 0x20u) ? 0x40 : 0);
}
