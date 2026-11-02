#include "fuel.h"
#include "mixture_internal.h"
#include "reference_math.h"
/* 7EB2..7F20. Rounded delta wraps as a word; both products truncate. */
PcmStatus pcm_fuel_map_acceleration(Pcm *pcm)
{
    uint16_t current = (uint16_t)((uint16_t)pcm->spark.load_coordinate << 8);
    if (current <= pcm->fuel.map_history) { pcm->fuel.map_delta = 0; goto inactive; }
    pcm->fuel.map_delta = (uint8_t)((uint16_t)(current - pcm->fuel.map_history + 128u) >> 8);
    MIX_CAL();
    uint8_t threshold = cal->map_threshold[pcm->spark.idle_state ? 1 : 0];
    if (pcm->reference.throttle <= cal->map_closed_throttle) threshold = mix_byte(2u * threshold);
    if (pcm->fuel.map_delta <= threshold) goto inactive;
    uint8_t value, gain;
    MIX_RUN(pcm_lookup_scaled(pcm->fuel.map_delta, &cal->ae_map, &value));
    if (pcm->reference.throttle > cal->map_double_throttle) value = mix_byte(2u * value);
    MIX_RUN(mix_h1(pcm->reference.rpm_coordinate, 16, &cal->ae_rpm, &gain));
    value = mix_double(value, gain);
    pcm->fuel.map_ae = mix_byte(((uint16_t)value * pcm->fuel.map_ae_gain) >> 5);
    pcm->fuel.map_acceleration = true;
    return PCM_OK;
inactive:
    pcm->fuel.map_acceleration = false;
    pcm->fuel.map_ae = 0;
    return PCM_OK;
}
