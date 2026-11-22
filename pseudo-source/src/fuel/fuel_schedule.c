#include "fuel.h"
#include "board_io.h"
#include "../system/system_internal.h"
/*852C..8547. Phase is sampled again after the battery/capture callee. */
PcmStatus pcm_fuel_schedule(Pcm *pcm)
{
    if (!(pcm->scheduler.phase&2u)) {
        SYS_RUN(pcm_oxygen_control(pcm));return pcm_vss_calculate(pcm);
    }
    SYS_RUN(pcm_fuel_battery_state(pcm));
    return (pcm->scheduler.phase&4u)?pcm_fuel_afr_learning(pcm):pcm_governor_target(pcm);
}
