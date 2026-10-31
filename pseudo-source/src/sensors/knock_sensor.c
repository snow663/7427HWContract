#include "knock.h"
#include "hardware.h"
#define RUN(call) do { PcmStatus result = (call); if (result != PCM_OK) return result; } while (0)
/* CEDB..CF15. External mux selector0, ADCTL=01, result ADR4. Even a bounded
 * ADC timeout reaches the sample. Literal SEI/CLI is not a mask restoration. */
PcmStatus pcm_knock_sensor(Pcm *pcm)
{
    if (pcm->calibration == NULL) return PCM_BAD_CONFIGURATION;
    if (!(pcm->calibration->reference.diagnostic_options & 0x10u)) return PCM_OK;
    RUN(pcm_adc_mux(pcm, 0));
    RUN(pcm_mask_irq(pcm, true));
    RUN(pcm_adc_convert(pcm, 1));
    RUN(pcm_mask_irq(pcm, false));
    uint8_t sample;
    RUN(pcm_read8(pcm, PCM_ADR4, &sample));
    const PcmKnockCalibration *cal = &pcm->calibration->knock;
    if (sample > cal->sensor_upper || sample < cal->sensor_lower) {
        if (pcm->knock.sensor_fault_count > cal->sensor_fault_delay)
            pcm->knock.sensor_fault = true;
        else ++pcm->knock.sensor_fault_count; /* Byte wrap, including delay=255. */
    } else {
        pcm->knock.sensor_fault = false;
        pcm->knock.sensor_fault_count = 0;
    }
    return PCM_OK;
}
