#include "startup.h"
/* 7100..711C: target assembly must establish SP/CCR and the timed INIT,
 * OPTION, TMSK2, OPT2 and BPROT prelude before C entry. This binding verifies
 * that precondition; it must never reset SP inside an active C call frame. */
PcmStatus pcm_reset_entry(Pcm *pcm)
{
    return pcm_run_task(pcm, PCM_RESET_ENTRY);
}
