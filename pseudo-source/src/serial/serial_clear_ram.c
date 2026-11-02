#include "serial_internal.h"
/*717F..7189. The boot loop clears0360..03FE;03FF is deliberately retained.
 * This is not the earlier working/retained-memory reset stage. */
PcmStatus pcm_serial_clear_ram(Pcm *pcm)
{
    for (uint16_t a=0x360;a<0x3ff;++a) { SER_RUN(pcm_serial_memory_write8(pcm,a,0)); }
    return PCM_OK;
}
