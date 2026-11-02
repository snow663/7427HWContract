#include "iac.h"
/* A407..A465: exited represents the discarded local return frame. Kicker
 * service uses the raw923C/9222 setters, not their larger wrappers. */
PcmStatus pcm_iac_service(Pcm *pcm, bool *exited)
{
    if (exited == NULL) return PCM_BAD_CONFIGURATION;
    *exited = false;
    if (pcm->reference.latch_inhibited || (pcm->iac.state_flags & 1u)) return PCM_OK;
    if (pcm->iac.service_reset) { *exited = true;return pcm_iac_reset_request(pcm); }
    bool target = (pcm->spark.service_flags & 1u) != 0;
    if (target == pcm->iac.service_kicker) return PCM_OK;
    if (target) {
        if (pcm->spark.service_flags & 2u) {
            pcm->spark.iac_desired_speed = pcm->iac.service_value;
            pcm->iac.transfer_flags |= 0x40u;
        } else {
            pcm->iac.context &= (uint8_t)~0x0cu;
            pcm->iac.target = pcm->iac.service_value;
            *exited = true;
        }
    } else {
        *exited = true;
        pcm->iac.kicker_request = !pcm->iac.service_kicker_value;
        if (pcm->iac.service_kicker_value) pcm->iac.kicker_flags |= 4u;
        else pcm->iac.kicker_flags &= (uint8_t)~4u;
    }
    return PCM_OK;
}
