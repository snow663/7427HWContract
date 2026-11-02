#include "hardware.h"
#define RUN(call) do { PcmStatus result = (call); if (result != PCM_OK) return result; } while (0)
/* F245..F25E. The caller owns masking. Even timeout continues to sample. */
PcmStatus pcm_adc_inputs(Pcm *pcm)
{
    RUN(pcm_adc_convert(pcm, 0x14));
    uint8_t sample;
    RUN(pcm_read8(pcm, PCM_ADR1, &sample));
    pcm->fuel.raw_throttle = sample;
    if (!pcm->reference.sample_map) {
        RUN(pcm_read8(pcm, PCM_ADR2, &sample));
        pcm->reference.map_sample = sample;
    }
    RUN(pcm_read8(pcm, PCM_ADR3, &sample));
    pcm->fuel.raw_oxygen = sample;
    return PCM_OK;
}
