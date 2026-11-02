#include "control.h"
#include "hardware.h"
#define RUN(call) do { PcmStatus result = (call); if (result != PCM_OK) return result; } while (0)
/* 7B70..7B9A, after the separate91A3 step call. The channel7 wait has no
 * factory timeout. F245's later conversion has its own twelve-poll limit. */
PcmStatus pcm_adc_feedback(Pcm *pcm)
{
    RUN(pcm_mask_irq(pcm, true));
    RUN(pcm_write8(pcm, PCM_ADCTL, 7));
    uint8_t status;
    do { RUN(pcm_read8(pcm, PCM_ADCTL, &status)); } while (!(status & 0x80u));
    uint16_t sum = 0;
    for (unsigned i = 0; i < 4; ++i) {
        uint8_t sample;
        RUN(pcm_read8(pcm, (uint16_t)(PCM_ADR1 + i), &sample));
        sum = (uint16_t)(sum + sample);
    }
    pcm->fuel.measured_current = (uint8_t)((sum + 2u) >> 2);
    RUN(pcm_adc_inputs(pcm));
    return pcm_mask_irq(pcm, false);
}
