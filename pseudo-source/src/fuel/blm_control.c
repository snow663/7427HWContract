#include "fuel.h"
#include "feedback_internal.h"
#include "hardware.h"
/*Contiguous8C73..8EB3, including the existing8DEF history producer. */
PcmStatus pcm_blm_control(Pcm *pcm)
{
    FB_RUN(pcm_blm_select(pcm));FB_RUN(pcm_blm_transition(pcm));
    FB_RUN(pcm_fuel_decel_history(pcm));return pcm_blm_learn(pcm);
}
