#include "scheduler.h"
#include "control.h"
#include "../system/system_internal.h"

/* 7B03..7B13. D472 runs even when D3B0 retains the catalyst state. */
PcmStatus pcm_slot_05(Pcm *pcm)
{
    if (pcm == NULL || pcm->calibration == NULL) return PCM_BAD_CONFIGURATION;
    SYS_RUN(pcm_catalyst_estimate(pcm));
    SYS_RUN(pcm_manifold_tuning(pcm));
    if (pcm->calibration->mode_f & 0x40u) return PCM_OK;
    return pcm_tcc_qualification(pcm);
}
