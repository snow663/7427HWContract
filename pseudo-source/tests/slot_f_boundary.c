#include "scheduler.h"
/* Historical foreground-refresh fixture supplies the earlier slotF producer
 * boundary. The slotF/kernel suites check the complete resident implementation. */
PcmStatus pcm_slot_0f(Pcm *pcm)
{
    PcmStatus status=pcm_run_task(pcm,PCM_SLOT_0F);
    if (status!=PCM_OK) return status;
    pcm->runtime.refresh_requested=true;return PCM_OK;
}
