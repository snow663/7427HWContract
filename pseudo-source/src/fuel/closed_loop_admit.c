#include "fuel.h"
#include "feedback_internal.h"
#include "hardware.h"
/* E477..E561. Service polarity here differs from the faster I/P admission. */
PcmStatus pcm_closed_loop_admit(Pcm *pcm)
{
    if (!pcm->runtime.fuel_running) goto disabled;
    if (pcm->fuel.oxygen_fault_a || pcm->fuel.oxygen_fault_b || pcm->fuel.alternate_afr_limit ||
        ((pcm->spark.map_fault || pcm->fuel.oxygen_idle_fault) && pcm->spark.idle_state)) {
        pcm->fuel.oxygen_age = 0;
        goto disabled;
    }
    FB_CAL();
    if (pcm->runtime.engine_service && pcm->fuel.oxygen_service) {
        if (!pcm->fuel.oxygen_service_value) goto disabled;
        goto closed;
    }
    if (pcm->fuel.oxygen_age < cal->activity_age_limit) ++pcm->fuel.oxygen_age;
    else pcm->fuel.oxygen_activity = false;
    if (!pcm->fuel.oxygen_activity) goto disabled;
    if (!pcm->runtime.diagnostic_switch && !pcm->fuel.oxygen_warmed) {
        uint8_t elapsed = (uint8_t)(pcm->scheduler.run_counter >> 1);
        unsigned index = pcm->iac.starting_coolant > cal->starting_coolant[1] ? 2u :
            pcm->iac.starting_coolant <= cal->starting_coolant[0] ? 1u : 0u;
        if (elapsed < cal->warmup_time[index]) {
            pcm->fuel.warmup_control = true;
            if (pcm->fuel.commanded_afr < cal->warmup_afr) goto disabled;
            goto clear_closed;
        }
        pcm->fuel.oxygen_warmed = true;
        pcm->fuel.warmup_control = false;
    }
    if (pcm->reference.coolant <= cal->closed_coolant ||
        (pcm->scheduler.profiling_enabled && (pcm->fuel.module_state & 3u))) goto clear_closed;
closed:
    pcm->fuel.closed_seen = true;
    pcm->io.coolant_context |= 0xa0u;
    if (pcm->fuel.idle_afr_ready) {
        pcm->io.coolant_context &= 0x7du;
        return PCM_OK;
    }
    {
        uint8_t load = (pcm->calibration->reference.mode_e & 1u) ? pcm->spark.normalized_load : pcm->spark.map_filtered;
        if (!(pcm->spark.load_status & 0x48u) && pcm->reference.coolant > cal->learning_coolant &&
            pcm->fuel.commanded_afr == cal->stoich && pcm->spark.vacuum <= cal->learning_vacuum &&
            load <= cal->learning_load[1] && load >= cal->learning_load[0] && pcm->reference.rpm_coordinate < cal->learning_rpm)
            pcm->io.coolant_context |= 2u;
        else pcm->io.coolant_context &= 0xfdu;
    }
    return PCM_OK;
disabled:
    pcm->fuel.warmup_control = false;
clear_closed:
    pcm->io.coolant_context &= 0x5du;
    return PCM_OK;
}
