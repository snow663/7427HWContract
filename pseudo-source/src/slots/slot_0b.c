#include "scheduler.h"
/* Reference 7B3D, table word 7A9B.
 * Stock body: 7B3D:D4EB;7B40:C514
 * Body binding required unless state-only slot E. */
PcmStatus pcm_slot_0b(Pcm *pcm)
{
    return pcm_run_task(pcm, PCM_SLOT_0B);
}
