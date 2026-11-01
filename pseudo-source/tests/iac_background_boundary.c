#include "control.h"
/* Earlier slot7 output/probe tests isolate their then-unported9E99 dependency.
 * Production, kernel and background-IAC tests link the resident body instead. */
PcmStatus pcm_iac_background(Pcm *pcm)
{
    return pcm_run_task(pcm, PCM_IAC_BACKGROUND);
}
