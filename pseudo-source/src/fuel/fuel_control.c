#include "control.h"
#include "fuel.h"

/* Factory fast dispatcher root at $7D4B. Default remains an explicit
 * source/target contract boundary. For host investigations only, the
 * platform can opt into the contiguous resident $7D4B..$8547 C cycle,
 * but ONLY when named fuel-prefix RAM aliases are enabled. Nothing here
 * unconditionally changes OEM target scheduling or flashes an injector. */
PcmStatus pcm_fuel_control(Pcm *pcm)
{
    if(pcm==NULL || pcm->platform==NULL)return PCM_BAD_CONFIGURATION;
    if(!pcm->platform->enable_resident_fuel_cycle)
        return pcm_run_task(pcm,PCM_FUEL_CONTROL);
    if(!pcm->platform->bind_fuel_ram_owners)return PCM_BAD_CONFIGURATION;
    return pcm_fuel_cycle(pcm);
}
