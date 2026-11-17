#include "scheduler.h"
#define RUN(call) do { PcmStatus result=(call);if(result!=PCM_OK)return result; } while(0)

/* $797A onwards: this is the fast-service/dispatcher continuation AFTER the
 * target has either accepted the saved X or completed LDS #$03F6.
 * Do not call this function after a recovery boundary unless the caller has
 * established that new HC11 stack. The C call/return frame is not its ABI. */
PcmStatus pcm_periodic_irq_resume(Pcm *pcm)
{
    RUN(pcm_fast_service(pcm));
    if (pcm->scheduler.busy) {
        pcm->scheduler.busy_phase=pcm->scheduler.phase;
        pcm->scheduler.pending=true;
        return PCM_OK;
    }
    return pcm_dispatcher(pcm);
}
