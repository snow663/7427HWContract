#include "scheduler.h"
/* Reference 7B39, table word 7A99.
 * Stock body: 7B39:D2B2
 * Body binding required unless state-only slot E. */
PcmStatus pcm_slot_0a(Pcm *pcm)
{
    return pcm_run_task(pcm, PCM_SLOT_0A);
}
