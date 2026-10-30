#include "control.h"
/* Reference 7D4B: Ignition handling and scheduled fuel group.
 * Contract boundary: body not ported. An explicit platform binding is required. */
PcmStatus pcm_fuel_control(Pcm *pcm)
{
    return pcm_run_task(pcm, PCM_FUEL_CONTROL);
}
