#include "control.h"
#include "fuel.h"
#include "../system/system_internal.h"
/* Reconciled factory $7D4B root. PR48's separately ROM-verified resident
 * controller is the default source implementation. The closure branch's
 * independent source-cycle reconstruction remains selectable for research,
 * and requires opt-in canonical RAM binding. Neither route implies a
 * compiled native HC11 BIN or physical injector authorization. */
PcmStatus pcm_fuel_control(Pcm *pcm)
{
    if(pcm==NULL || pcm->platform==NULL)return PCM_BAD_CONFIGURATION;
    if(pcm->platform->enable_resident_fuel_cycle) {
        if(!pcm->platform->bind_fuel_ram_owners)return PCM_BAD_CONFIGURATION;
        return pcm_fuel_cycle(pcm);
    }
    SYS_RUN(pcm_fuel_ignition(pcm));
    SYS_RUN(pcm_fuel_inputs(pcm));
    SYS_RUN(pcm_fuel_calculate(pcm));
    return pcm_fuel_schedule(pcm);
}
