#ifndef PSEUDO_SOURCE_FUEL_H
#define PSEUDO_SOURCE_FUEL_H
#include "pcm.h"
/* Initial scheduled-fuel ignition and watchdog prefix, BMHM $7D4B..$7DB5.
 * The later input/tail dispatch is not wired until all ordered callees exist. */
PcmStatus pcm_fuel_ignition_precheck(Pcm *);
/* $7DB6..$7E4E, follows precheck; $90D3 governor remains a gated dependency. */
PcmStatus pcm_fuel_input_precalculate(Pcm *);
/* Contiguous $7D4B..$7E4E callable source; not yet the scheduled fuel root. */
PcmStatus pcm_fuel_input_prefix(Pcm *);
/* $852C phase-dependent tail, guarded $8EB4 governor target. */
PcmStatus pcm_fuel_scheduled_tail(Pcm *);
/* Complete $7D4B..$8547 callable cycle, not yet installed in fast dispatch. */
PcmStatus pcm_fuel_cycle(Pcm *);
PcmStatus pcm_fuel_governor_target(Pcm *);
/* BMHM $90D3..$9166: proportional/integral governor command to board306C. */
PcmStatus pcm_fuel_governor_drive(Pcm *);
/* BMHM $8EC9..$8EDA: unsigned RPM-target difference and 0075.2 direction. */
PcmStatus pcm_fuel_governor_error(Pcm *);
/* BMHM $8EE4..$8F3A: fourfold VSS delta, 0075 latches and TPS seed. */
PcmStatus pcm_fuel_governor_vss_gate(Pcm *);
/* $8F3B..$8F5C: signed target-error TPS gate, control path selector. */
PcmStatus pcm_fuel_governor_tps_mode(Pcm *,bool *ordinary);
/* BMHM $8F5F..$90D2: separate rate, ordinary, lead and final command stages. */
PcmStatus pcm_fuel_governor_rate(Pcm *);
PcmStatus pcm_fuel_governor_ordinary(Pcm *,uint8_t *candidate);
PcmStatus pcm_fuel_governor_lead(Pcm *,uint8_t *candidate);
PcmStatus pcm_fuel_governor_finish(Pcm *,uint8_t candidate);
PcmStatus pcm_fuel_governor_compute(Pcm *,bool ordinary);
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

/* Cut/decel, reservoirs and admitted running delivery. */
PcmStatus pcm_fuel_cut_gate(Pcm *pcm, bool *reduce);
PcmStatus pcm_fuel_acceleration_reservoir(Pcm *pcm);
PcmStatus pcm_fuel_decel_gate(Pcm *pcm, bool *reduce);
PcmStatus pcm_fuel_reduction(Pcm *pcm);
PcmStatus pcm_fuel_enleanment(Pcm *pcm);
PcmStatus pcm_fuel_cut_decel(Pcm *pcm);
PcmStatus pcm_fuel_cpi_prepare(Pcm *pcm);
PcmStatus pcm_fuel_async_accumulate(Pcm *pcm);
PcmStatus pcm_fuel_packet_select(Pcm *pcm, uint16_t *packet, bool *emit);
PcmStatus pcm_fuel_packet_emit(Pcm *pcm, uint16_t packet);
PcmStatus pcm_fuel_packet(Pcm *pcm);
PcmStatus pcm_fuel_route(Pcm *pcm, bool *packet);
PcmStatus pcm_fuel_deliver(Pcm *pcm);
PcmStatus pcm_fuel_construct(Pcm *pcm);
PcmStatus pcm_fuel_running(Pcm *pcm);
PcmStatus pcm_fuel_calculate(Pcm *pcm);
#endif
