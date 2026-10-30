#include "hardware.h"
/* Reference FFD6 -> F7EA. Target entry/RTI preserves the real interrupt frame.
 * No ordinary nesting is opened by the resident body. Not ported yet. */
PcmStatus pcm_sci_irq(Pcm *pcm)
{
    return pcm_run_task(pcm, PCM_SCI_BODY);
}
