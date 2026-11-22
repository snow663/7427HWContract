#include "control.h"
/* Historical spark-dispatch fixture; real EGR flow is checked separately. */
PcmStatus pcm_egr_flow(Pcm *pcm) { return pcm_run_task(pcm,PCM_EGR_FLOW); }
