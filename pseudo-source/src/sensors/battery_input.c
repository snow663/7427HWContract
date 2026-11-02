#include "hardware.h"
#define RUN(call) do { PcmStatus result = (call); if (result != PCM_OK) return result; } while (0)
/* C56F..C582. Mux outside SEI; publish the sampled byte only after CLI. */
PcmStatus pcm_battery_input(Pcm *pcm)
{
    RUN(pcm_adc_mux(pcm, 2));
    RUN(pcm_mask_irq(pcm, true));
    RUN(pcm_adc_convert(pcm, 1));
    uint8_t sample;
    RUN(pcm_read8(pcm, PCM_ADR4, &sample));
    RUN(pcm_mask_irq(pcm, false));
    pcm->reference.battery = sample;
    return PCM_OK;
}
