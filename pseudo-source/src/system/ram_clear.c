#include "system.h"
#define RUN(call) do { PcmStatus result=(call);if (result!=PCM_OK) return result; } while (0)
/* F2FD..F325. Preserve byte alignment by count (not address), word width,
 * low-byte block count and the do/while behavior for a zero block count. */
PcmStatus pcm_ram_clear(Pcm *pcm,uint16_t address,uint16_t count)
{
    while (count&7u) {
        RUN(pcm_write8(pcm,address,0));
        address=(uint16_t)(address+1u);
        if (--count==0) return PCM_OK;
    }
    uint8_t blocks=(uint8_t)(count>>3);
    do {
        for (unsigned offset=0;offset<8;offset+=2)
            RUN(pcm_write16(pcm,(uint16_t)(address+offset),0));
        address=(uint16_t)(address+8u);
    } while (--blocks!=0);
    return PCM_OK;
}
