#include "fuel.h"
#include "feedback_internal.h"
#include "hardware.h"
/*88E9..891D. Encoded signed PW correction, neutral128 before encoding. */
PcmStatus pcm_oxygen_combine(Pcm *pcm)
{
    uint8_t combined;
    if (!(pcm->io.coolant_context & 0x40u)) combined = mix_byte((unsigned)pcm->fuel.proportional+pcm->fuel.integrator);
    else {
        if (pcm->calibration == NULL) return PCM_BAD_CONFIGURATION;
        if ((pcm->calibration->reference.mode_b & 8u) && pcm->fuel.fuel_activity) {
            FB_CAL();
            if (cal->proportional_cap < pcm->fuel.proportional) pcm->fuel.proportional = cal->proportional_cap;
        }
        combined = mix_sub(pcm->fuel.integrator,pcm->fuel.proportional);
    }
    pcm->fuel.feedback_encoded = (uint8_t)(combined-128u);
    return PCM_OK;
}
