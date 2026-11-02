#include "control.h"
/* D4DA..D4EA, slot9 VSS filtering; resident body remains explicit. */
PcmStatus pcm_vss_filter(Pcm *pcm)
{ return pcm_run_task(pcm, PCM_VSS_FILTER); }
