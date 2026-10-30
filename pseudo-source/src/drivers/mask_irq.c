#include "pcm.h"
/* A literal SEI/CLI-style assignment, not an assumed previous-mask restore. */
PcmStatus pcm_mask_irq(Pcm *pcm, bool masked)
{
    if (pcm->platform == NULL || pcm->platform->mask_irq == NULL) return PCM_NO_HARDWARE;
    return pcm->platform->mask_irq(pcm->platform->context, masked);
}
