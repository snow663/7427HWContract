#include "scheduler.h"
/* Reference 7AA6, table word 7A85.
 * Stock body: 7AA6:C56F;7AA9:CF15
 * Body binding required unless state-only slot E. */
PcmStatus pcm_slot_00(Pcm *pcm)
{
    return pcm_run_task(pcm, PCM_SLOT_00);
}
