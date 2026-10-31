#include "hardware.h"
/* F275..F27F, rooted callers X=3000. Two distinct PORTD reads are required. */
PcmStatus pcm_adc_mux(Pcm *pcm, uint8_t selector)
{
    PcmStatus result = pcm_update8(pcm, PCM_PORTD, 0x38, 0);
    if (result != PCM_OK) return result;
    uint8_t port;
    result = pcm_read8(pcm, PCM_PORTD, &port);
    if (result != PCM_OK) return result;
    return pcm_write8(pcm, PCM_PORTD, (uint8_t)(port | (uint8_t)(selector << 3)));
}
