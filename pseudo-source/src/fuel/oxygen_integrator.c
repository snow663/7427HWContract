#include "fuel.h"
#include "feedback_internal.h"
#include "hardware.h"
/*886F..88CC. Equality stops preserve byte wrap for corrupt initial INT values. */
PcmStatus pcm_oxygen_integrator(Pcm *pcm)
{
    bool direction = (pcm->io.coolant_context & 0x40u) != 0;
    if (direction != pcm->fuel.oxygen_error_positive) return PCM_OK;
    FB_CAL();
    if ((uint8_t)(2u*pcm->fuel.oxygen_error) <= cal->integrator_deadband) { pcm->fuel.integrator_delay = 0; return PCM_OK; }
    uint8_t delay = pcm->fuel.integrator_delay < pcm->fuel.oxygen_interval ? (uint8_t)(pcm->fuel.integrator_delay+1u) : 0;
    pcm->fuel.integrator_delay = delay;
    if (delay != 0) return PCM_OK;
    uint8_t integrator = pcm->fuel.integrator;
    if (!pcm->fuel.oxygen_error_positive) {
        if (integrator != cal->integrator_maximum && (!pcm->fuel.warmup_control || integrator < 128)) ++integrator;
    } else {
        if ((pcm->calibration->reference.mode_b & 8u) && pcm->fuel.fuel_activity) return PCM_OK;
        if (integrator != cal->integrator_minimum && !pcm->fuel.short_pulse) --integrator;
    }
    pcm->fuel.integrator = integrator;
    return PCM_OK;
}
