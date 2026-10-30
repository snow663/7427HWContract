#include "hardware.h"
/* One literal byte read/modify/write. Callers own any required IRQ mask. */
PcmStatus pcm_update8(Pcm *pcm, uint16_t address, uint8_t clear, uint8_t set)
{
    uint8_t value;
    PcmStatus result = pcm_read8(pcm, address, &value);
    if (result != PCM_OK) return result;
    return pcm_write8(pcm, address, (uint8_t)((value & (uint8_t)~clear) | set));
}
