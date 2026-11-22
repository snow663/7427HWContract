#include "fuel.h"
#include "../system/system_internal.h"
/*E286..E561. Temperature and offset always precede the phase-bit4 gate;
 * AE/startup/closed-loop producers run only on the lower phase half. */
PcmStatus pcm_fuel_slow(Pcm *pcm)
{
    SYS_RUN(pcm_pump_feedback(pcm));SYS_RUN(pcm_fuel_charge_temperature(pcm));
    SYS_RUN(pcm_injector_offset(pcm));if (pcm->scheduler.phase&0x10u) return PCM_OK;
    SYS_RUN(pcm_fuel_transient_gains(pcm));SYS_RUN(pcm_fuel_startup(pcm));
    return pcm_closed_loop_admit(pcm);
}
