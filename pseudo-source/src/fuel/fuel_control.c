#include "control.h"
#include "fuel.h"
#include "../system/system_internal.h"
/*7D4B..8547. Resident ignition/input/calculation/tail join. STOP and optional
 * external modules remain explicit boundaries at their actual admissions. */
PcmStatus pcm_fuel_control(Pcm *pcm)
{
    SYS_RUN(pcm_fuel_ignition(pcm));SYS_RUN(pcm_fuel_inputs(pcm));
    SYS_RUN(pcm_fuel_calculate(pcm));return pcm_fuel_schedule(pcm);
}
