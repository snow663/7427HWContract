#include "scheduler.h"
/* Reference 7B14, table word 7A91.
 * Stock body: 7B14:CB15;7B17:CE10
 * Body binding required unless state-only slot E. */
PcmStatus pcm_slot_06(Pcm *pcm)
{
    return pcm_run_task(pcm, PCM_SLOT_06);
}
