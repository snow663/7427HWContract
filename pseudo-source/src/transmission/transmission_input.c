#include "control.h"
/* Reference AE85: Input wrapper ending in F781 then F64E.
 * Contract boundary: body not ported. An explicit platform binding is required. */
PcmStatus pcm_transmission_input(Pcm *pcm)
{
    return pcm_run_task(pcm, PCM_TRANSMISSION_INPUT);
}
