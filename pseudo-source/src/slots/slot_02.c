#include "scheduler.h"
/* Reference 7AB7, table word 7A89.
 * Stock body: 7AB8:F20D
 * Body binding required unless state-only slot E. */
PcmStatus pcm_slot_02(Pcm *pcm)
{
    PcmStatus result = pcm_mask_irq(pcm, true);
    if (result != PCM_OK) return result;
    result = pcm_run_task(pcm, PCM_SLOT_02);
    if (result != PCM_OK) return result;
    return pcm_mask_irq(pcm, false);
}
