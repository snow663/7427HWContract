#include "scheduler.h"
/* Reference 7B52, table word 7AA1.
 * Stock body: no calls; sets $0004 bit2 if $0051 bit2 still set
 * Body binding required unless state-only slot E. */
PcmStatus pcm_slot_0e(Pcm *pcm)
{
    if (pcm->runtime.refresh_requested) pcm->runtime.refresh_late = true;
    return PCM_OK;
}
