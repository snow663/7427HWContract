#include "fuel.h"
#include "mixture_internal.h"
/* 899B..8A21. Selected AFR stays in A until8A88, exposed here as an output. */
PcmStatus pcm_fuel_afr_idle(Pcm *pcm, uint8_t *afr)
{
    if (afr == NULL) return PCM_BAD_CONFIGURATION;
    MIX_CAL();
    uint8_t value = pcm->fuel.commanded_afr;
    if (pcm->spark.vehicle_speed_high > cal->idle_speed || pcm->reference.throttle > cal->idle_throttle) {
        if (pcm->scheduler.run_counter >= cal->idle_runtime) pcm->iac.startup_cancel = true;
        pcm->spark.idle_state = false;
        goto reset;
    }
    pcm->spark.idle_state = true;
    if (pcm->io.environmental_load > value) goto reset;
    if (pcm->reference.coolant <= cal->idle_coolant) {
        pcm->fuel.idle_afr_ready = true;
        *afr = pcm->io.environmental_load;
        return PCM_OK;
    }
    if (cal->idle_entry_delay != 0) {
        if (!(pcm->calibration->reference.mode_b & 2u) && pcm->iac.park_neutral) goto reset;
        if (pcm->fuel.idle_afr_ready) {
            if (pcm->fuel.idle_afr_count > cal->idle_apply_delay) { *afr = pcm->io.environmental_load; return PCM_OK; }
            goto count;
        }
        if (pcm->fuel.idle_afr_count <= cal->idle_entry_delay) goto count;
    }
    {
        uint8_t integrator = pcm->fuel.integrator;
        uint8_t error = integrator >= 128 ? (uint8_t)(integrator - 128) : (uint8_t)(128 - integrator);
        if (error <= cal->idle_integrator_limit) {
            pcm->fuel.idle_afr_ready = true;
            pcm->fuel.idle_afr_count = 0;
            *afr = value;
            return PCM_OK;
        }
    }
count:
    if (pcm->scheduler.phase == 0x27u) ++pcm->fuel.idle_afr_count;
    *afr = value;
    return PCM_OK;
reset:
    pcm->fuel.idle_afr_ready = false;
    pcm->fuel.idle_afr_count = 0;
    *afr = value;
    return PCM_OK;
}
