#include "hardware.h"
#define RUN(call) do { PcmStatus result = (call); if (result != PCM_OK) return result; } while (0)
/* F20D..F244 ->F25E. Slot2 and boot own masking. All three conversions retain
 * the F25F timeout-and-still-sample behavior and separate PORTD reads. */
PcmStatus pcm_adc_auxiliary(Pcm *pcm)
{
    uint8_t sample;
    RUN(pcm_adc_mux(pcm, 7));
    RUN(pcm_adc_convert(pcm, 1));
    RUN(pcm_read8(pcm, PCM_ADR4, &sample));
    pcm->io.raw_coolant = sample;
    RUN(pcm_adc_mux(pcm, 6));
    RUN(pcm_adc_convert(pcm, 1));
    RUN(pcm_read8(pcm, PCM_ADR4, &sample));
    pcm->io.auxiliary_sample = sample;
    RUN(pcm_adc_mux(pcm, 1));
    RUN(pcm_adc_convert(pcm, 0x11));
    RUN(pcm_read8(pcm, PCM_ADR2, &sample));
    pcm->io.diagnostic_sample = sample;
    RUN(pcm_read8(pcm, PCM_ADR3, &sample));
    pcm->io.auxiliary_reference = sample;
    RUN(pcm_read8(pcm, PCM_ADR4, &sample));
    pcm->spark.battery_sample = sample;
    return PCM_OK;
}
