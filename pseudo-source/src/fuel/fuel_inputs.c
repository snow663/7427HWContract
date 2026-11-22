#include "fuel.h"
#include "board_io.h"
#include "../system/system_internal.h"
/*7DB6..7E4E. Keep MAP context, previous TPS and oxygen age before governor
 * output and density. Governor option is sampled at its consuming position. */
PcmStatus pcm_fuel_inputs(Pcm *pcm)
{
    SYS_RUN(pcm_map_transient(pcm));SYS_RUN(pcm_fuel_throttle(pcm));
    SYS_RUN(pcm_fuel_oxygen_filter(pcm));uint8_t option;
    SYS_RUN(pcm_read8(pcm,0x400f,&option));
    if (option&1u) SYS_RUN(pcm_governor_actuator(pcm));
    return pcm_fuel_density(pcm);
}
