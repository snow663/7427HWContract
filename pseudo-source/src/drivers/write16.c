#include "pcm.h"
/* Preserve the transaction width; do not infer word coherency or replace
 * ordered device operations with a generic memory copy. */
PcmStatus pcm_write16(Pcm *pcm, uint16_t address, uint16_t value)
{
    if (pcm->platform == NULL || pcm->platform->write16 == NULL) return PCM_NO_HARDWARE;
    return pcm->platform->write16(pcm->platform->context, address, value);
}
