#include "control.h"
/* Reference D1F6: EGR position and duty controller.
 * Contract boundary: body not ported. An explicit platform binding is required. */
PcmStatus pcm_egr_control(Pcm *pcm)
{
    return pcm_run_task(pcm, PCM_EGR_CONTROL);
}
