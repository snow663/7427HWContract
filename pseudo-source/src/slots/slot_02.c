#include "scheduler.h"
#include "hardware.h"
/*7AB7..7ABC: the complete auxiliary ADC scan under literal SEI/CLI. */
PcmStatus pcm_slot_02(Pcm *pcm)
{
    PcmStatus result = pcm_mask_irq(pcm, true);
    if (result != PCM_OK) return result;
    result = pcm_adc_auxiliary(pcm);
    if (result != PCM_OK) return result;
    return pcm_mask_irq(pcm, false);
}
