#include "control.h"
/* Reference F5E8: Serial polling and optional broadcast schedule.
 * Contract boundary: body not ported. An explicit platform binding is required. */
PcmStatus pcm_serial_poll(Pcm *pcm)
{
    return pcm_run_task(pcm, PCM_SERIAL_POLL);
}
