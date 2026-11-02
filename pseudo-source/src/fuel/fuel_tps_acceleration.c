#include "fuel.h"
#include "mixture_internal.h"
#include "reference_math.h"
/* 7F21..7F85. Entry hysteresis precedes TPS-history update on phase bit1. */
PcmStatus pcm_fuel_tps_acceleration(Pcm *pcm)
{
    uint8_t old = (uint8_t)(pcm->fuel.tps_history >> 8), value = 0;
    if (pcm->reference.throttle <= old) goto inactive;
    value = (uint8_t)(pcm->reference.throttle - old);
    if ((pcm->fuel.tps_history & 128u) && --value == 0) goto inactive;
    MIX_CAL();
    if (!pcm->fuel.tps_acceleration && value <= cal->tps_threshold) goto inactive;
    value = pcm_lookup16(mix_byte(2u * value), cal->tps_curve);
    if (pcm->spark.vehicle_speed_high < cal->tps_speed_limit) value = mix_double_round(value, cal->tps_speed_gain);
    value = mix_double_round(value, pcm->io.tps_ae_factor);
    pcm->fuel.tps_acceleration = true;
    goto store;
inactive:
    value = 0;
    pcm->fuel.tps_acceleration = false;
store:
    pcm->fuel.tps_ae = value;
    if (pcm->scheduler.phase & 2u) pcm->fuel.tps_history = pcm_lag8(pcm->reference.throttle, pcm->fuel.tps_history, pcm->io.environmental_trim);
    return PCM_OK;
}
