#include "fuel.h"
#include "delivery_internal.h"
#include "hardware.h"
/*8058..82EC, including the shared80FC multiplier call. */
PcmStatus pcm_fuel_cut_decel(Pcm *pcm)
{
    bool reduce;DL_RUN(pcm_fuel_cut_gate(pcm,&reduce));
    if (reduce) return pcm_fuel_reduction(pcm);
    DL_RUN(pcm_fuel_acceleration_reservoir(pcm));DL_RUN(pcm_fuel_decel_gate(pcm,&reduce));
    return reduce ? pcm_fuel_reduction(pcm) : pcm_fuel_enleanment(pcm);
}
