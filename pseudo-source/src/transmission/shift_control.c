#include "control.h"
#include "../system/system_internal.h"

/* $B32D..$B333. The shift observer consumes the movement state from $B334. */
PcmStatus pcm_shift_control(Pcm *pcm)
{
    SYS_RUN(pcm_transmission_movement(pcm));
    return pcm_shift_observation(pcm);
}
