#include "control.h"
/* Reference CDF7: EGR hardware command publication.
 * Contract boundary: body not ported. An explicit platform binding is required. */
PcmStatus pcm_egr_output(Pcm *pcm)
{
    return pcm_run_task(pcm, PCM_EGR_OUTPUT);
}
