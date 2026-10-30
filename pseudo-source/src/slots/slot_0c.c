#include "scheduler.h"
/* Reference 7B44, table word 7A9D.
 * Stock body: 7B44:CC35
 * Body binding required unless state-only slot E. */
PcmStatus pcm_slot_0c(Pcm *pcm)
{
    return pcm_run_task(pcm, PCM_SLOT_0C);
}
