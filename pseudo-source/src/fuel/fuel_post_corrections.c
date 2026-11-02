#include "fuel.h"
#include "feedback_internal.h"
#include "hardware.h"
/*Contiguous82ED..83B0. Earlier cut/decel/AE-reservoir logic stays separate. */
PcmStatus pcm_fuel_post_corrections(Pcm *pcm)
{
    FB_RUN(pcm_fuel_derivative_correction(pcm));FB_RUN(pcm_fuel_baro_battery(pcm));
    return pcm_fuel_feedback_apply(pcm);
}
