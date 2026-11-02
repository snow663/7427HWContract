#include "fuel.h"
#include "mixture_internal.h"
#include "reference_math.h"
/* 85B2..8612. Overflow at the first doubling returns before TPS lookup. */
PcmStatus pcm_fuel_crank_pulse(Pcm *pcm, uint16_t *pulse)
{
    if (pulse == NULL) return PCM_BAD_CONFIGURATION;
    MIX_CAL();
    uint16_t value = pcm_gain_word(cal->crank_base, pcm_lookup16(pcm->reference.coolant, cal->crank_coolant));
    if (pcm->reference.event_age > cal->crank_age) {
        uint8_t coordinate;
        PcmStatus result = pcm_fuel_crank_coordinate(pcm, &coordinate);
        if (result != PCM_OK) return result;
        value = pcm_gain_word(value, pcm_lookup16(coordinate, pcm->scheduler.clear_after_run_count ? cal->crank_hot : cal->crank_normal));
    }
    value = pcm_gain_word(value, pcm_lookup16(mix_sub(pcm->spark.barometric_pressure, 96), cal->crank_baro));
    if (value > 32767u) { *pulse = UINT16_MAX; return PCM_OK; }
    value = (uint16_t)(2u * value);
    uint8_t gain;
    PcmStatus result = pcm_lookup_scaled(pcm->reference.throttle, &cal->crank_tps, &gain);
    if (result != PCM_OK) return result;
    *pulse = mix_word(4u * pcm_gain_word(value, gain));
    return PCM_OK;
}
