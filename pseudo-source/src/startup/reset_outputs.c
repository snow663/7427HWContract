#include "startup.h"
/* Reference stage 7144..7164: Literal ASIC initialization and output transaction sequence.
 * Stage boundary only; exact instruction/call order still needs a target port. */
PcmStatus pcm_reset_outputs(Pcm *pcm)
{
    return pcm_run_task(pcm, PCM_RESET_OUTPUTS);
}
