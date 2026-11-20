#include "fuel.h"
#define F_RUN(call) do { PcmStatus s=(call);if(s!=PCM_OK)return s; } while(0)

/* BMHM $7D4B..$8547. Callable ordered composition of the stock ignition/
 * input prefix, crank/running calculation, and phase-selected scheduled
 * continuation. This is NOT automatically admitted by fast dispatch:
 * active $90D3/$8EC9 governor paths, selected logical RAM bindings and
 * full source/ROM histories must close before replacing PCM_FUEL_CONTROL. */
PcmStatus pcm_fuel_cycle(Pcm *pcm)
{
    F_RUN(pcm_fuel_input_prefix(pcm));
    F_RUN(pcm_fuel_calculate(pcm));
    return pcm_fuel_scheduled_tail(pcm);
}
