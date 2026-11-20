#include "fuel.h"

/* BMHM $8EB4..$8EC8: early source gates and default target. The eligible
 * $8EC9+ governor body remains an explicit task, not a guessed command. */
PcmStatus pcm_fuel_governor_target(Pcm *pcm)
{
    if (pcm==NULL || pcm->calibration==NULL) return PCM_BAD_CONFIGURATION;
    if (!(pcm->calibration->mode_f&1u) || !pcm->runtime.spark_running) {
        pcm->transmission.governor_requested_throttle=255;
        return PCM_OK;
    }
    uint8_t status;
    PcmStatus result=pcm_read8(pcm,0x006f,&status);
    if (result!=PCM_OK) return result;
    if (status&0x34u) {
        pcm->transmission.governor_requested_throttle=255;
        return PCM_OK;
    }
    return pcm_run_task(pcm,PCM_GOVERNOR_TARGET);
}
