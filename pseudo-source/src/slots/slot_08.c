#include "scheduler.h"
/* Reference 7B2B, table word 7A95.
 * Stock body: 7B2B:CEBB
 * Body binding required unless state-only slot E. */
PcmStatus pcm_slot_08(Pcm *pcm)
{
    return pcm_run_task(pcm, PCM_SLOT_08);
}
