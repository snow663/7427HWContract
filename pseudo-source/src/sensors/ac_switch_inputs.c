#include "control.h"
/* CB15..CC34: AC and diagnostic-switch input owner, before slot6 learning.
 * This explicit boundary replaces the former whole-slot6 binding. */
PcmStatus pcm_ac_switch_inputs(Pcm *pcm)
{
    return pcm_run_task(pcm, PCM_AC_SWITCH_INPUTS);
}
