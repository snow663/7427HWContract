#include "scheduler.h"
/* Reference 7AAD, table word 7A87.
 * Stock body: 7AAD:C583;7AB0:C668;7AB3:ADAA
 * Body binding required unless state-only slot E. */
PcmStatus pcm_slot_01(Pcm *pcm)
{
    return pcm_run_task(pcm, PCM_SLOT_01);
}
