#include "scheduler.h"
/* Reference 7ABD, table word 7A8B.
 * Stock body: 7ABD:F5CF;7AC0:D4EB;7AC3:C514
 * Body binding required unless state-only slot E. */
PcmStatus pcm_slot_03(Pcm *pcm)
{
    return pcm_run_task(pcm, PCM_SLOT_03);
}
