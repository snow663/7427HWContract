#include "fuel.h"
#include "feedback_internal.h"
#include "hardware.h"
/*86F2..878F. true admits8790; false has performed the neutral return. */
PcmStatus pcm_oxygen_admit(Pcm *pcm, bool *control)
{
    if (control == NULL) return PCM_BAD_CONFIGURATION;
    *control = false;
    if (pcm->runtime.engine_service && pcm->fuel.oxygen_service) {
        if (pcm->fuel.oxygen_service_value) goto reset;
        goto admitted;
    }
    if (!(pcm->io.coolant_context & 0x80u) && !pcm->fuel.warmup_control) return pcm_oxygen_neutral(pcm);
    if (pcm->runtime.deceleration_fuel_cut || pcm->runtime.power_enrichment || pcm->fuel.output_rich_cap) goto inhibited;
    FB_CAL();
    (void)cal;
    uint8_t mode = pcm->calibration->reference.mode_c;
    if ((mode & 0x20u) && pcm->fuel.enrichment_entry) {
        pcm->fuel.enrichment_entry = false;
        goto reset;
    }
    if ((mode & 0x50u) && pcm->fuel.blm_transition) goto reset;
    if (pcm->fuel.ve_reset_request) { pcm->fuel.ve_reset_request = false; goto reset; }
    if (pcm->fuel.decel_enleanment) {
        if ((pcm->io.coolant_context & 0x40u) || pcm->fuel.integrator < 128) goto admitted;
        goto reset;
    }
    if (pcm->spark.load_coordinate > cal->control_load || pcm->reference.rpm_coordinate <= cal->control_rpm_lower ||
        pcm->reference.rpm_coordinate > cal->control_rpm_upper || pcm->spark.vehicle_speed_high < cal->control_speed ||
        (pcm->io.coolant_context & 0x40u) || pcm->fuel.integrator < 128) goto admitted;
inhibited:
    pcm->fuel.oxygen_notification = true;
reset:
    pcm->fuel.asynchronous_active = true;
    return pcm_oxygen_neutral(pcm);
admitted:
    *control = true;
    return PCM_OK;
}
