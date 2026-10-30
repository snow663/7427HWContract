#include "startup.h"
/* Reference stage 7392..7431: Controller state seeds and hardware baselines.
 * Stage boundary only; exact instruction/call order still needs a target port. */
PcmStatus pcm_reset_controllers(Pcm *pcm)
{
    return pcm_run_task(pcm, PCM_RESET_CONTROLLERS);
}
