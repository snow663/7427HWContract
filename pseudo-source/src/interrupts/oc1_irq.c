#include "hardware.h"
/* Reference FFE8 -> CE7C. Target entry/RTI preserves the real interrupt frame.
 * No ordinary nesting is opened by the resident body. Not ported yet. */
PcmStatus pcm_oc1_irq(Pcm *pcm)
{
    return pcm_run_task(pcm, PCM_OC1_BODY);
}
