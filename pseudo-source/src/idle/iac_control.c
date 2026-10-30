#include "control.h"
/* Reference 93D0: Main idle-air controller with service escapes.
 * Contract boundary: body not ported. An explicit platform binding is required. */
PcmStatus pcm_iac_control(Pcm *pcm)
{
    return pcm_run_task(pcm, PCM_IAC_CONTROL);
}
