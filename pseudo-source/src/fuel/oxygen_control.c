#include "fuel.h"
#include "feedback_internal.h"
#include "hardware.h"
/* Contiguous863D..891D, preserving the early neutral return. */
PcmStatus pcm_oxygen_control(Pcm *pcm)
{
    bool admitted;uint8_t window;
    FB_RUN(pcm_oxygen_activity(pcm));FB_RUN(pcm_oxygen_thresholds(pcm));FB_RUN(pcm_oxygen_direction(pcm));
    FB_RUN(pcm_oxygen_admit(pcm,&admitted));
    if (!admitted) return PCM_OK;
    FB_RUN(pcm_oxygen_proportional(pcm,&window));FB_RUN(pcm_oxygen_integrator(pcm));
    FB_RUN(pcm_oxygen_window(pcm,window));return pcm_oxygen_combine(pcm);
}
