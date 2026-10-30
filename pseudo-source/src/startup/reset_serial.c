#include "startup.h"
/* Reference stage 7431..7459: Phase-related startup context and serial setup.
 * Stage boundary only; exact instruction/call order still needs a target port. */
PcmStatus pcm_reset_serial(Pcm *pcm)
{
    return pcm_run_task(pcm, PCM_RESET_SERIAL);
}
