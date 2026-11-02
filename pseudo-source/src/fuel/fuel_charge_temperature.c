#include "fuel.h"
#include "reference_math.h"
/* E2C8..E2FA. The air-rate high byte is the existing shared0232 owner. */
PcmStatus pcm_fuel_charge_temperature(Pcm *pcm)
{
    if (pcm->calibration == NULL || pcm->calibration->air == NULL) return PCM_BAD_CONFIGURATION;
    const PcmAirCalibration *cal = pcm->calibration->air;
    uint8_t index = pcm->reference.coolant;
    if (pcm->calibration->reference.mode_b & 0x40u) {
        uint8_t weight = pcm_lookup16(pcm->iac.runtime_high, cal->charge_weight);
        uint8_t coolant = pcm->reference.coolant, mat = pcm->spark.mat_sample;
        uint8_t delta = coolant < mat ? 0 : (uint8_t)(coolant - mat);
        uint32_t blend = (uint32_t)weight * delta * 2u;
        if (blend > 65535u) index = 255;
        else {
            unsigned sum = (unsigned)(blend >> 8) + pcm->spark.mat_sample;
            index = sum > 255u ? 255u : (uint8_t)sum;
        }
    }
    uint8_t value = pcm_lookup16(index, cal->charge_curve);
    pcm->fuel.charge_temperature = (uint16_t)((uint16_t)value * 128u + 0x7480u);
    return PCM_OK;
}
