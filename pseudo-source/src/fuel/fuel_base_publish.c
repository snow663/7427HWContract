#include "fuel.h"
#include "reference_math.h"
static uint16_t fraction(uint16_t numerator, uint16_t denominator)
{
    return denominator == 0 || numerator >= denominator ? UINT16_MAX :
        (uint16_t)(((uint32_t)numerator << 16) / denominator);
}
static uint16_t cap(uint32_t value) { return value > 65535u ? 65535u : (uint16_t)value; }
/*7FD8..8031. Ordered state publication counterpart of the pure fuel_base
 * equation. Inputs are sampled at their consuming stages, not all at entry. */
PcmStatus pcm_fuel_base_publish(Pcm *pcm)
{
    if (pcm->calibration == NULL || pcm->calibration->air == NULL) return PCM_BAD_CONFIGURATION;
    const PcmAirCalibration *cal = pcm->calibration->air;
    uint16_t density = fraction(pcm->spark.density, pcm->fuel.charge_temperature);
    pcm->fuel.displaced = pcm_gain_word(density, cal->cylinder_volume);
    pcm->fuel.air_charge = pcm_gain_word(pcm->fuel.displaced, pcm->fuel.volumetric_efficiency);
    uint16_t period = pcm->spark.period;
    uint16_t rate = period == 0 ? UINT16_MAX : cap(2u * (((uint32_t)pcm->fuel.air_charge << 8) / period));
    pcm->iac.runtime_high = (uint8_t)(rate >> 8);
    pcm->fuel.air_rate_fraction = (uint8_t)rate;
    uint16_t mixture = fraction((uint16_t)(pcm->fuel.air_charge >> 2), (uint16_t)((uint16_t)pcm->fuel.commanded_afr << 8));
    uint16_t flow = cal->injector_flow;
    pcm->fuel.corrected_pulse = flow == 0 ? UINT16_MAX : cap(((uint32_t)mixture << 8) / flow);
    return PCM_OK;
}
