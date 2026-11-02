#include "control.h"
/* CF16..D03D, slot9 EGR demand producer; resident body remains explicit. */
PcmStatus pcm_egr_demand(Pcm *pcm)
{ return pcm_run_task(pcm, PCM_EGR_DEMAND); }
