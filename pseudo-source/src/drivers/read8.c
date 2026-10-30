#include "pcm.h"
/* Preserve the transaction width; do not infer word coherency or replace
 * ordered device operations with a generic memory copy. */
PcmStatus pcm_read8(Pcm *pcm, uint16_t address, uint8_t *value)
{
    if (pcm->platform == NULL || pcm->platform->read8 == NULL) return PCM_NO_HARDWARE;
    return pcm->platform->read8(pcm->platform->context, address, value);
}
