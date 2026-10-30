#include "pcm.h"
/* Preserve the transaction width; do not infer word coherency or replace
 * ordered device operations with a generic memory copy. */
PcmStatus pcm_write8(Pcm *pcm, uint16_t address, uint8_t value)
{
    if (pcm->platform == NULL || pcm->platform->write8 == NULL) return PCM_NO_HARDWARE;
    return pcm->platform->write8(pcm->platform->context, address, value);
}
