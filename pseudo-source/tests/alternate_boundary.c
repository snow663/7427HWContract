#include "control.h"
/* Link-time isolation only for the earlier admission/period/output suites.
 * Kernel and complete-controller tests link the real resident adapter instead.
 * Keeping this outside src/ prevents a production runtime override or bypass. */
PcmStatus pcm_alternate_rpm(Pcm *pcm)
{
    return pcm_run_task(pcm, PCM_ALTERNATE_RPM);
}
