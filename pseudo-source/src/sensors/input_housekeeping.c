#include "control.h"
/* Reference 9167: AC and park/neutral input housekeeping.
 * Contract boundary: body not ported. An explicit platform binding is required. */
PcmStatus pcm_input_housekeeping(Pcm *pcm)
{
    return pcm_run_task(pcm, PCM_INPUT_HOUSEKEEPING);
}
