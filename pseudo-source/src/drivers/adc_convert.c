#include "hardware.h"
/* F25F..F274, rooted callers X=3000. Caller owns literal masking. Timeout
 * sets flags and returns normally; it does not suppress the subsequent sample. */
PcmStatus pcm_adc_convert(Pcm *pcm, uint8_t control)
{
    pcm->runtime.adc_timeout = false;
    PcmStatus result = pcm_write8(pcm, PCM_ADCTL, control);
    if (result != PCM_OK) return result;
    for (unsigned poll = 0; poll < 12; ++poll) {
        uint8_t status;
        result = pcm_read8(pcm, PCM_ADCTL, &status);
        if (result != PCM_OK) return result;
        if (status & 0x80u) return PCM_OK;
    }
    pcm->runtime.adc_fault = true;
    pcm->runtime.adc_timeout = true;
    return PCM_OK;
}
