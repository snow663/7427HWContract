#include "serial_internal.h"
/* Logical address interface: owned serial RAM is native; other addresses bind
 * through the explicit address-space provider, including ROM and live devices. */
PcmStatus pcm_serial_memory_read8(Pcm *pcm,uint16_t address,uint8_t *out)
{
    if (out==NULL) return PCM_BAD_CONFIGURATION;
    return ser_get(pcm,address,out) ? PCM_OK : pcm_read8(pcm,address,out);
}
