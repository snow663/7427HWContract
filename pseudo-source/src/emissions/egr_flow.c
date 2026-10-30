#include "control.h"
/* Reference D03E: EGR flow calculation.
 * Contract boundary: body not ported. An explicit platform binding is required. */
PcmStatus pcm_egr_flow(Pcm *pcm)
{
    return pcm_run_task(pcm, PCM_EGR_FLOW);
}
