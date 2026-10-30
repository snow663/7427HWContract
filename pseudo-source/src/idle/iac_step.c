#include "control.h"
/* Reference 91A3: Per-tick idle-air phase service.
 * Contract boundary: body not ported. An explicit platform binding is required. */
PcmStatus pcm_iac_step(Pcm *pcm)
{
    return pcm_run_task(pcm, PCM_IAC_STEP);
}
