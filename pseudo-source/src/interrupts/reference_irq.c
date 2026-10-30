#include "hardware.h"
/* FFF2 ->74EA..77C6. Hardware entry/RTI and the real frame remain target
 * assembly responsibilities. Both C stages preserve the masked-entry contract. */
PcmStatus pcm_reference_irq(Pcm *pcm)
{
    PcmStatus result = pcm_reference_prefix(pcm);
    return result == PCM_OK ? pcm_reference_event(pcm) : result;
}
