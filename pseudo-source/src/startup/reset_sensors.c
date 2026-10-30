#include "startup.h"
/* Reference stage 718A..71C3: Initial samples and factory-mode admission boundary.
 * Stage boundary only; exact instruction/call order still needs a target port. */
PcmStatus pcm_reset_sensors(Pcm *pcm)
{
    return pcm_run_task(pcm, PCM_RESET_SENSORS);
}
