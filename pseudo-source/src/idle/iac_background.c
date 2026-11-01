#include "control.h"
/* 9E99 entry: background IAC/kicker body and its stopped-engine tail.
 * Named dependency before slot7's resident CA6B spark auxiliaries. */
PcmStatus pcm_iac_background(Pcm *pcm)
{
    return pcm_run_task(pcm, PCM_IAC_BACKGROUND);
}
