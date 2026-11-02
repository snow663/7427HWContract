#include "fuel.h"
#include "feedback_internal.h"
#include "hardware.h"
/*Contiguous891E..8EB3. A missing AFR extension stops before BLM. */
PcmStatus pcm_fuel_afr_learning(Pcm *pcm)
{
    FB_RUN(pcm_fuel_afr(pcm));return pcm_blm_control(pcm);
}
