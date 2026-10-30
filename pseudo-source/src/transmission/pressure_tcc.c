#include "control.h"
/* Reference B56B: Pressure and TCC progress group.
 * Contract boundary: body not ported. An explicit platform binding is required. */
PcmStatus pcm_pressure_tcc(Pcm *pcm)
{
    return pcm_run_task(pcm, PCM_PRESSURE_TCC);
}
