#ifndef PSEUDO_SOURCE_FUEL_H
#define PSEUDO_SOURCE_FUEL_H
#include "pcm.h"
PcmStatus pcm_fuel_finalize(Pcm *);
PcmStatus pcm_fuel_publish(Pcm *, uint16_t pulse);
PcmStatus pcm_injector_offset(Pcm *);
PcmStatus pcm_fuel_battery_state(Pcm *);
PcmStatus pcm_fuel_throttle(Pcm *);
PcmStatus pcm_fuel_density(Pcm *);
PcmStatus pcm_fuel_charge_temperature(Pcm *);
PcmStatus pcm_fuel_ve(Pcm *);
PcmStatus pcm_fuel_base_publish(Pcm *);
PcmStatus pcm_fuel_air_charge(Pcm *);

/* Callable mixture stages; broad scheduled fuel/slot roots retain their remaining work. */
PcmStatus pcm_fuel_authorize(Pcm *pcm);
PcmStatus pcm_fuel_oxygen_filter(Pcm *pcm);
PcmStatus pcm_fuel_crank_coordinate(Pcm *pcm, uint8_t *coordinate);
PcmStatus pcm_fuel_crank_pulse(Pcm *pcm, uint16_t *pulse);
PcmStatus pcm_fuel_crank_prepare(Pcm *pcm);
PcmStatus pcm_fuel_admit(Pcm *pcm, bool *running);
PcmStatus pcm_fuel_map_acceleration(Pcm *pcm);
PcmStatus pcm_fuel_tps_acceleration(Pcm *pcm);
PcmStatus pcm_fuel_acceleration(Pcm *pcm);
PcmStatus pcm_fuel_transient_gains(Pcm *pcm);
PcmStatus pcm_fuel_decel_history(Pcm *pcm);
PcmStatus pcm_fuel_startup_seed(Pcm *pcm);
PcmStatus pcm_fuel_startup_context(Pcm *pcm);
PcmStatus pcm_fuel_startup_afr(Pcm *pcm);
PcmStatus pcm_fuel_startup_spark(Pcm *pcm);
PcmStatus pcm_fuel_startup(Pcm *pcm);
PcmStatus pcm_fuel_afr_base(Pcm *pcm);
PcmStatus pcm_fuel_afr_idle(Pcm *pcm, uint8_t *afr);
PcmStatus pcm_fuel_afr_bias(Pcm *pcm, uint8_t value);
PcmStatus pcm_fuel_pe(Pcm *pcm);
PcmStatus pcm_fuel_afr_finish(Pcm *pcm);
PcmStatus pcm_fuel_afr(Pcm *pcm);

/* O2/BLM and callable pulse-correction stages. */
PcmStatus pcm_oxygen_activity(Pcm *pcm);
PcmStatus pcm_closed_loop_admit(Pcm *pcm);
PcmStatus pcm_oxygen_thresholds(Pcm *pcm);
PcmStatus pcm_oxygen_direction(Pcm *pcm);
PcmStatus pcm_oxygen_neutral(Pcm *pcm);
PcmStatus pcm_oxygen_admit(Pcm *pcm, bool *control);
PcmStatus pcm_oxygen_proportional(Pcm *pcm, uint8_t *window);
PcmStatus pcm_oxygen_integrator(Pcm *pcm);
PcmStatus pcm_oxygen_window(Pcm *pcm, uint8_t window);
PcmStatus pcm_oxygen_combine(Pcm *pcm);
PcmStatus pcm_oxygen_control(Pcm *pcm);
PcmStatus pcm_blm_reset(Pcm *pcm);
PcmStatus pcm_blm_boot_clamp(Pcm *pcm);
PcmStatus pcm_blm_select(Pcm *pcm);
PcmStatus pcm_blm_transition(Pcm *pcm);
PcmStatus pcm_blm_learn(Pcm *pcm);
PcmStatus pcm_blm_control(Pcm *pcm);
PcmStatus pcm_fuel_afr_learning(Pcm *pcm);
PcmStatus pcm_fuel_pulse_scale(Pcm *pcm, uint8_t gain);
PcmStatus pcm_fuel_blm_scale(Pcm *pcm, uint8_t gain);
PcmStatus pcm_fuel_egr_blm(Pcm *pcm);
PcmStatus pcm_fuel_derivative_correction(Pcm *pcm);
PcmStatus pcm_fuel_baro_battery(Pcm *pcm);
PcmStatus pcm_fuel_feedback_apply(Pcm *pcm);
PcmStatus pcm_fuel_post_corrections(Pcm *pcm);
#endif
