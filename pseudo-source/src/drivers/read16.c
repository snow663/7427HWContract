#include "pcm.h"
/* Preserve the transaction width; do not infer word coherency or replace
 * ordered device operations with a generic memory copy. */
PcmStatus pcm_read16(Pcm *pcm, uint16_t address, uint16_t *value)
{
    if (pcm->platform == NULL || pcm->platform->read16 == NULL) return PCM_NO_HARDWARE;
    return pcm->platform->read16(pcm->platform->context, address, value);
}
