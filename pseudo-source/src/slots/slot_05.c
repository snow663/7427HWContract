#include "scheduler.h"
/* Reference 7B03, table word 7A8F.
 * Stock body: 7B03:D3B0;7B06:D472;7B10:C6BB
 * Body binding required unless state-only slot E. */
PcmStatus pcm_slot_05(Pcm *pcm)
{
    return pcm_run_task(pcm, PCM_SLOT_05);
}
