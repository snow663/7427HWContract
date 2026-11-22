#include "control.h"
/* Historical IAC/input slice fixture. Current kernel and EGR producer suite
 * link the real CF16 body and keep their ROM comparisons separate. */
PcmStatus pcm_egr_demand(Pcm *pcm)
{ return pcm_run_task(pcm,PCM_EGR_DEMAND); }
