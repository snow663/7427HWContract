#include "control.h"
/* Reference AC51: Alternate reference-period RPM and board-request path.
 * Contract boundary: body not ported. An explicit platform binding is required. */
PcmStatus pcm_alternate_rpm(Pcm *pcm)
{
    return pcm_run_task(pcm, PCM_ALTERNATE_RPM);
}
