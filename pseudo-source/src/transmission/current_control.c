#include "control.h"
/* Reference 7C13: Current-control calculation producing014C; hardware meaning stays scoped.
 * Contract boundary: body not ported. An explicit platform binding is required. */
PcmStatus pcm_current_control(Pcm *pcm)
{
    return pcm_run_task(pcm, PCM_CURRENT_CONTROL);
}
