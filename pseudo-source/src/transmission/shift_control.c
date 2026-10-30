#include "control.h"
/* Reference B32D: Shift progress group.
 * Contract boundary: body not ported. An explicit platform binding is required. */
PcmStatus pcm_shift_control(Pcm *pcm)
{
    return pcm_run_task(pcm, PCM_SHIFT_CONTROL);
}
