#include "hardware.h"
#include "interrupts.h"
/* FFF2 ->74EA..77C6, or FC11's factory leaf. Hardware entry/RTI and the real
 * frame remain target responsibilities. The prefix samples the mode once. */
PcmStatus pcm_reference_irq(Pcm *pcm)
{
    PcmStatus result = pcm_reference_prefix(pcm);
    if (result==PCM_FACTORY_BOUNDARY) return pcm_factory_reference_irq(pcm);
    return result == PCM_OK ? pcm_reference_event(pcm) : result;
}
