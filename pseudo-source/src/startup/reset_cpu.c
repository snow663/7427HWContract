#include "startup.h"
/* Reference stage 7100..7144: CPU mode register relocation and chip-select setup.
 * Stage boundary only; exact instruction/call order still needs a target port. */
PcmStatus pcm_reset_cpu(Pcm *pcm)
{
    return pcm_run_task(pcm, PCM_RESET_CPU);
}
