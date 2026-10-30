#include "hardware.h"
#define RUN(call) do { PcmStatus result = (call); if (result != PCM_OK) return result; } while (0)
/* 751B..77C6. ASLD plus three MUL instructions supply33 nominal E cycles
 * between the ADCTL write and ADR1 sample. No invented ADC polling occurs. */
PcmStatus pcm_reference_event(Pcm *pcm)
{
    if (pcm->calibration == NULL) return PCM_BAD_CONFIGURATION;
    if (pcm->reference.sample_map) {
        RUN(pcm_write8(pcm, PCM_ADCTL, 5));
        RUN(pcm_delay_cycles(pcm, 33));
        uint8_t sample;
        RUN(pcm_read8(pcm, PCM_ADR1, &sample));
        pcm->reference.map_sample = sample;
    }
    return pcm->runtime.fuel_running ? pcm_reference_run(pcm) : pcm_reference_crank(pcm);
}
