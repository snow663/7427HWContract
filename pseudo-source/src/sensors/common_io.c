#include "control.h"
/* Reference 7BA7: Board flush MAP filtering and speed input sampling.
 * Contract boundary: body not ported. An explicit platform binding is required. */
PcmStatus pcm_common_io(Pcm *pcm)
{
    return pcm_run_task(pcm, PCM_COMMON_IO);
}
