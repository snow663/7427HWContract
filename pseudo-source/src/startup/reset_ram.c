#include "startup.h"
/* Reference stage 7164..718A: Working and serial RAM initialization.
 * Stage boundary only; exact instruction/call order still needs a target port. */
PcmStatus pcm_reset_ram(Pcm *pcm)
{
    return pcm_run_task(pcm, PCM_RESET_RAM);
}
