#include "fuel.h"

/* BMHM $8EB4..$8EC8 default gates and resident $8EC9..$8EDA
 * direction/magnitude. The $8EDB..$90D2 governing body remains an
 * explicit task including optional $1809 carry/flags semantics. */
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
    result=pcm_fuel_governor_error(pcm);
    if(result!=PCM_OK)return result;
    return pcm_run_task(pcm,PCM_GOVERNOR_TARGET);
}
