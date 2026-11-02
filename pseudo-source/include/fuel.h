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
#endif
