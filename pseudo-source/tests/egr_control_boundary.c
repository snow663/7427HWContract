#include "control.h"
/* Historical spark-dispatch fixture: preserve its original non-spark task.
 * The EGR and kernel suites link and check the resident implementation. */
PcmStatus pcm_egr_control(Pcm *pcm) { return pcm_run_task(pcm,PCM_EGR_CONTROL); }
