#include "hardware.h"
/* Reference FFF2 -> 74EA. Target entry/RTI preserves the real interrupt frame.
 * No ordinary nesting is opened by the resident body. Not ported yet. */
PcmStatus pcm_reference_irq(Pcm *pcm)
{
    return pcm_run_task(pcm, PCM_REFERENCE_BODY);
}
