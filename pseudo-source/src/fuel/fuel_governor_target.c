#include "fuel.h"

/* BMHM $8EB4..$8F3A: default, error and VSS gates are resident.
 * The optional $1809 task must supply both carry and accumulator-A
 * result through the explicit transient fields. $8F3B..$90D2 remains
 * a named dependency, rather than a guessed governor control policy. */
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
    if(pcm->scheduler.profiling_enabled) { /* $8EDB: optional $1809 */
        result=pcm_run_task(pcm,PCM_GOVERNOR_HEADSUP);
        if(result!=PCM_OK)return result;
        if(pcm->transmission.governor_headsup_carry) {
            pcm->transmission.governor_requested_throttle=
                pcm->transmission.governor_headsup_result; /* $8EC5 */
            return PCM_OK;
        }
    }
    result=pcm_fuel_governor_vss_gate(pcm);
    if(result!=PCM_OK)return result;
    bool ordinary;
    result=pcm_fuel_governor_tps_mode(pcm,&ordinary);
    if(result!=PCM_OK)return result;
    /* The named continuation owns both $8F5F and $9010 successors.
     * Its task binding can inspect $0075; no guessed branch is run. */
    return pcm_run_task(pcm,PCM_GOVERNOR_TARGET);
}
