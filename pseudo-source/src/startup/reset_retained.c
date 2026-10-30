#include "startup.h"
/* Reference stage 71C3..7392: ROM validation retained checksums and recovery bookkeeping.
 * Stage boundary only; exact instruction/call order still needs a target port. */
PcmStatus pcm_reset_retained(Pcm *pcm)
{
    return pcm_run_task(pcm, PCM_RESET_RETAINED);
}
