#include "fuel.h"
#define F_RUN(call) do { PcmStatus s=(call);if(s!=PCM_OK)return s; } while(0)

/* BMHM $7D4B..$8547. Callable ordered composition of the stock ignition/
 * input prefix, crank/running calculation, and phase-selected scheduled
 * continuation. The independent alternative is selected by pcm_fuel_control
 * only when enable_resident_fuel_cycle and bind_fuel_ram_owners are both set.
 * The default fast path uses PR48's resident controller. Both paths retain
 * explicit optional modules and need a native RAM/peripheral backend. */
PcmStatus pcm_fuel_cycle(Pcm *pcm)
{
    F_RUN(pcm_fuel_input_prefix(pcm));
    F_RUN(pcm_fuel_calculate(pcm));
    return pcm_fuel_scheduled_tail(pcm);
}
