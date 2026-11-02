#include "fuel.h"
/* 7E4F..7EB1. false means the common852C tail is next; true admits AE/VE.
 * Ignition/off handling and the preceding TPS/O2/density work are separate. */
PcmStatus pcm_fuel_admit(Pcm *pcm, bool *running)
{
    if (running == NULL) return PCM_BAD_CONFIGURATION;
    *running = false;
    if (!pcm->runtime.fuel_running) return pcm_fuel_crank_prepare(pcm);
    PcmStatus result = pcm_fuel_authorize(pcm);
    if (result != PCM_OK) return result;
    if (!pcm->fuel.authorized) return pcm_fuel_publish(pcm, 0);
    *running = true;
    return PCM_OK;
}
