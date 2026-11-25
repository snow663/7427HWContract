#include "interrupts.h"
#include "output_timer_internal.h"

/* FFE0 ->7875..78D8: OC5/IC4 source, literal OC5 output-timer body.
 * The physical pin/device mode and native entry/RTI remain platform-owned. */
PcmStatus pcm_toc5_irq(Pcm *pcm)
{
    return output_timer_irq(pcm, false);
}
