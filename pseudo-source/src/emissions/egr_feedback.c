#include "control.h"
/* Reference D14E: EGR feedback acquisition and closed-reference handling.
 * Contract boundary: body not ported. An explicit platform binding is required. */
PcmStatus pcm_egr_feedback(Pcm *pcm)
{
    return pcm_run_task(pcm, PCM_EGR_FEEDBACK);
}
