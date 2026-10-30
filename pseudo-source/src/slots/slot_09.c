#include "scheduler.h"
/* Reference 7B2F, table word 7A97.
 * Stock body: 7B2F:CF16;7B32:A2B0;7B35:D4DA
 * Body binding required unless state-only slot E. */
PcmStatus pcm_slot_09(Pcm *pcm)
{
    return pcm_run_task(pcm, PCM_SLOT_09);
}
