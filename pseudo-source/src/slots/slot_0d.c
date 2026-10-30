#include "scheduler.h"
/* Reference 7B48, table word 7A9F.
 * Stock body: 7B48:CCC1;7B4B:DBFB;7B4E:DC89
 * Body binding required unless state-only slot E. */
PcmStatus pcm_slot_0d(Pcm *pcm)
{
    return pcm_run_task(pcm, PCM_SLOT_0D);
}
