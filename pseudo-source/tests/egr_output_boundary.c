#include "control.h"
/* Historical spark-dispatch fixture; real EGR output is checked separately. */
PcmStatus pcm_egr_output(Pcm *pcm) { return pcm_run_task(pcm,PCM_EGR_OUTPUT); }
