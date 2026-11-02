#include "fuel.h"
#include "delivery_internal.h"
#include "hardware.h"
/*Contiguous7EB2..83B0, for an already-admitted running-fuel invocation. */
PcmStatus pcm_fuel_construct(Pcm *pcm)
{
    DL_RUN(pcm_fuel_acceleration(pcm));DL_RUN(pcm_fuel_air_charge(pcm));DL_RUN(pcm_fuel_egr_blm(pcm));
    DL_RUN(pcm_fuel_cut_decel(pcm));return pcm_fuel_post_corrections(pcm);
}
