#include "serial_internal.h"
/* Serial-owned state is authoritative; foreign addresses fall back to the
 * physical/logical provider. This same owner is used by the opt-in RAM map. */
PcmStatus pcm_serial_memory_write8(Pcm *pcm,uint16_t a,uint8_t v)
{
    return ser_put(pcm,a,v) ? PCM_OK : pcm_write8(pcm,a,v);
}
