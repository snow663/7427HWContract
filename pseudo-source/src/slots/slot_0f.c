#include "scheduler.h"
/* Reference 7B5A, table word 7AA3.
 * Stock body: 7B5A:C514;7B5D:C4F5;7B60:E62D;7B63:E6E5;7B66:E286
 * Body binding required unless state-only slot E. */
PcmStatus pcm_slot_0f(Pcm *pcm)
{
    PcmStatus result = pcm_run_task(pcm, PCM_SLOT_0F);
    if (result != PCM_OK) return result;
    pcm->runtime.refresh_requested = true;
    return PCM_OK;
}
