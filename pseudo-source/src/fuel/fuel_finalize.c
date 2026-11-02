#include "fuel.h"
#include "reference_math.h"
/* 84BC..852B. The synchronous short-PW lookup is unconditional for nonzero
 * widths below0100;400E.4 selects shaping only in the separate async helper. */
PcmStatus pcm_fuel_finalize(Pcm *pcm)
{
    uint16_t pulse = pcm->fuel.corrected_pulse;
    if (pcm->io.coolant_context & 0x10u) {
        pcm->reference.delivered_pulse = pulse;
        pcm->fuel.short_pulse = false;
        return PCM_OK; /* Async bypass retains0250 and emits no3FCE write. */
    }
    if (pulse != 0) {
        if (pcm->calibration == NULL || pcm->calibration->fuel == NULL) return PCM_BAD_CONFIGURATION;
        const PcmFuelCalibration *cal = pcm->calibration->fuel;
        bool borrow = false;
        if (pulse < 256) {
            uint8_t input = pulse < 32 ? 0 : (uint8_t)(pulse - 32);
            pulse = (uint16_t)(pulse + pcm_lookup16(input, pcm->calibration->reference.short_pulse));
            borrow = pulse < pcm->calibration->reference.short_subtract;
            pulse = (uint16_t)(pulse - pcm->calibration->reference.short_subtract);
        }
        if (!borrow) pcm->fuel.short_pulse = false;
        if (borrow || pulse < cal->synchronous_minimum) {
            pcm->fuel.short_pulse = true;
            pulse = cal->synchronous_replacement;
        }
    }
    return pcm_fuel_publish(pcm, pulse);
}
