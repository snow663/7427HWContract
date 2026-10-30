#include "scheduler.h"
/* Reference 7AC7, table word 7A8D.
 * Stock body: 7AC7:C8B1;7ACE:B9EE;7AD1:B99F;7AD4:EAB1;7AD7:EAE4;7ADA:C8D6;7ADD:C8FD;7AE2:E75F;7AE5:E793;7AE8:C96A;7AEB:C9C0;7AEE:C9F7
 * Body binding required unless state-only slot E. */
PcmStatus pcm_slot_04(Pcm *pcm)
{
    return pcm_run_task(pcm, PCM_SLOT_04);
}
