#include "control.h"
/* Reference C4E5: TPS and transmission spark input group.
 * Contract boundary: body not ported. An explicit platform binding is required. */
PcmStatus pcm_transmission_spark(Pcm *pcm)
{
    return pcm_run_task(pcm, PCM_TRANSMISSION_SPARK);
}
