#include "scheduler.h"
#define RUN(call) do { PcmStatus result = (call); if (result != PCM_OK) return result; } while (0)

/* Reference 7989..7A84. Catch-up repeats main work without fast_service.
 * mask_irq(false) may expose a pending interrupt before the next busy store.
 * No synthetic missed-tick count or unconditional bounded catch-up is added. */
PcmStatus pcm_dispatcher(Pcm *pcm)
{
    for (;;) {
        pcm->scheduler.busy = true;
        RUN(pcm_main_pass(pcm));
        RUN(pcm_mask_irq(pcm, true));
        pcm->scheduler.busy = false;
        RUN(pcm_profile_tail(pcm));
        if (!pcm->scheduler.pending) return PCM_OK;
        pcm->scheduler.pending = false;
        RUN(pcm_mask_irq(pcm, false));
    }
}
