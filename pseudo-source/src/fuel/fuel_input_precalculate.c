#include "fuel.h"
#include "board_io.h"
#define F_RUN(call) do { PcmStatus s=(call); if(s!=PCM_OK)return s; } while(0)

/* BMHM $7DB6..$7E4E, after the separately ported ignition/COP prelude.
 * Each completed producer executes in source order. $90D3 governor duty
 * control is a resident callable body when $400F.0 is set; its actual
 * $306C board command still requires the physical hardware provider. The $7E4F crank/run
 * admission and $852C scheduled tail belong to the caller. */
PcmStatus pcm_fuel_input_precalculate(Pcm *pcm)
{
    if (pcm==NULL || pcm->calibration==NULL) return PCM_BAD_CONFIGURATION;
    F_RUN(pcm_map_transient(pcm));       /* 7DB6..7DF0 */
    F_RUN(pcm_fuel_throttle(pcm));       /* 7DF1..7E08 */
    F_RUN(pcm_fuel_oxygen_filter(pcm));  /* 7E09..7E35 */
    if (pcm->calibration->mode_f & 1u)
        F_RUN(pcm_fuel_governor_drive(pcm)); /* 7E36..7E3F, JSR 90D3 */
    return pcm_fuel_density(pcm);        /* 7E40..7E4E, FDIV+0A59 */
}
