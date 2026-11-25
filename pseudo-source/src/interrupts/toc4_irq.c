#include "interrupts.h"
#include "output_timer_internal.h"

/* FFE2 ->78D9..793C: literal OC4 output-timer body. Native interrupt entry,
 * physical output behavior and RTI remain explicit platform contracts. */
PcmStatus pcm_toc4_irq(Pcm *pcm)
{
    return output_timer_irq(pcm, true);
}
