#include "fuel.h"
#include "feedback_internal.h"
#include "hardware.h"
/*8D9E..8DEE. Classify wrapped BLM differences by the byte N bit. */
PcmStatus pcm_blm_transition(Pcm *pcm)
{
    if (pcm->calibration == NULL) return PCM_BAD_CONFIGURATION;
    if (pcm->calibration->reference.mode_c & 0x10u) return PCM_OK;
    FB_CAL();
    bool closed = pcm->reference.throttle < cal->idle_throttle;
    if (closed != pcm->fuel.blm_closed_throttle) pcm->fuel.blm_closed_throttle = closed;
    else {
        uint8_t delta = (uint8_t)(pcm->fuel.blm_previous-pcm->iac.blm_value);
        bool keep = delta != 0 && ((delta & 128u) ?
            ((uint8_t)(0u-delta) >= cal->transition_negative && pcm->fuel.integrator >= cal->transition_integrator_high) :
            (delta >= cal->transition_positive && pcm->fuel.integrator <= cal->transition_integrator_low));
        if (!keep) pcm->fuel.blm_transition = false;
    }
    pcm->fuel.blm_previous = pcm->iac.blm_value;
    return PCM_OK;
}
