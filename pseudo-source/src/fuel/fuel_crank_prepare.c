#include "fuel.h"
#include "mixture_internal.h"
#include "hardware.h"
#include "reference_math.h"
/* 7E53..7EA5, joining84F5..852B only when main-loop delivery is admitted.
 * The caller has selected nonrunning mode. Both paths stop before852C. */
PcmStatus pcm_fuel_crank_prepare(Pcm *pcm)
{
    MIX_RUN(pcm_fuel_authorize(pcm));
    pcm->fuel.map_history = (uint16_t)((uint16_t)pcm->spark.load_coordinate << 8);
    pcm->fuel.throttle_decel_filter = (uint16_t)((uint16_t)pcm->reference.throttle << 8);
    pcm->fuel.tps_history = pcm->fuel.throttle_decel_filter;
    uint16_t pulse;
    MIX_RUN(pcm_fuel_crank_pulse(pcm, &pulse));
    pcm->reference.crank_seed = mix_word(2u * pulse);
    MIX_RUN(pcm_battery_input(pcm));
    MIX_CAL();
    pcm->reference.crank_seed = pcm_gain_word(pcm->reference.crank_seed, pcm_lookup16(pcm->reference.battery, cal->crank_battery));
    if (pcm->calibration->reference.mode_c & 4u) return PCM_OK;
    if (pcm_lookup16(pcm->reference.coolant, pcm->calibration->reference.crank_skip) > pcm->reference.crank_references) return PCM_OK;
    return pcm_fuel_publish(pcm, pcm_crank_event_gain(pcm));
}
