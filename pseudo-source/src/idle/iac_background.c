#include "iac.h"
#define RUN(call) do { PcmStatus result = (call); if (result != PCM_OK) return result; } while (0)
/* 9E99..A2AF. A stopped call reaches snapshot publication without target,
 * learning, decay or hold-age work. No whole-body task binding remains. */
PcmStatus pcm_iac_background(Pcm *pcm)
{
    if (!pcm->runtime.spark_running) return pcm_iac_publish(pcm, false);
    if (pcm->calibration == NULL || pcm->calibration->iac == NULL) return PCM_BAD_CONFIGURATION;
    RUN(pcm_iac_desired(pcm));
    RUN(pcm_iac_movement(pcm));
    RUN(pcm_iac_kicker(pcm));
    RUN(pcm_iac_cold(pcm));
    RUN(pcm_iac_transition_decay(pcm));
    RUN(pcm_iac_transfer(pcm));
    return pcm_iac_publish(pcm, true);
}
