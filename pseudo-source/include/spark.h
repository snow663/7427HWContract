#ifndef PSEUDO_SOURCE_SPARK_H
#define PSEUDO_SOURCE_SPARK_H
#include "pcm.h"
/* Pure shared quotient/coordinate transform; either byte output may be NULL. */
uint16_t pcm_spark_coordinates(uint16_t basis, uint8_t *low, uint8_t *rounded);
PcmStatus pcm_spark_output_extension(Pcm *, uint8_t *magnitude);
PcmStatus pcm_spark_convert(Pcm *, uint16_t *saved);
PcmStatus pcm_spark_handoff(Pcm *, uint16_t saved);
PcmStatus pcm_spark_output(Pcm *);
/* Callable AC51 body, also reached through the resident alternate adapter. */
PcmStatus pcm_spark_alternate(Pcm *);
/* ABCB..AC50 monitor and shared ACA0/ACA3 cleanup. */
PcmStatus pcm_spark_monitor(Pcm *);
/* Stops after ABCA publication; pcm_spark_control also runs the monitor. */
PcmStatus pcm_spark_publish(Pcm *, bool *published);
PcmStatus pcm_spark_load(Pcm *);
PcmStatus pcm_spark_map_check(Pcm *);
PcmStatus pcm_spark_fuel_admit(Pcm *);
PcmStatus pcm_spark_timeout(Pcm *);
/* normal=true only at the A5E5 continuation. Alternate RPM is an explicit
 * dependency; TRAP_BOUNDARY identifies the first SWI without emulating it. */
PcmStatus pcm_spark_admit(Pcm *, bool *normal);
PcmStatus pcm_spark_prepare(Pcm *, bool *normal);
PcmStatus pcm_spark_period_sample(Pcm *);
PcmStatus pcm_spark_rpm_filters(Pcm *);
uint16_t pcm_spark_reference_term(uint16_t period);
PcmStatus pcm_spark_period_terms(Pcm *);
PcmStatus pcm_spark_precompute(Pcm *);
/* built=true only after a successful normal A466..AB43 calculation. */
PcmStatus pcm_spark_build(Pcm *, bool *built);
PcmStatus pcm_spark_base(Pcm *);
PcmStatus pcm_spark_coolant(Pcm *);
PcmStatus pcm_spark_altitude(Pcm *);
PcmStatus pcm_spark_egr(Pcm *);
PcmStatus pcm_spark_sum(Pcm *);
PcmStatus pcm_spark_mat_effect(Pcm *);
PcmStatus pcm_spark_mat(Pcm *);
PcmStatus pcm_spark_pe(Pcm *);
PcmStatus pcm_spark_auxiliary(Pcm *);
PcmStatus pcm_spark_terms(Pcm *);
PcmStatus pcm_spark_idle(Pcm *);
PcmStatus pcm_spark_transient(Pcm *);
PcmStatus pcm_spark_decel(Pcm *);
PcmStatus pcm_spark_modifiers(Pcm *);
PcmStatus pcm_spark_composite(Pcm *);
PcmStatus pcm_spark_extension(Pcm *);
PcmStatus pcm_spark_override(Pcm *);
PcmStatus pcm_spark_upper_limit(Pcm *);
PcmStatus pcm_spark_lower_limit(Pcm *);
PcmStatus pcm_spark_service(Pcm *);
PcmStatus pcm_spark_command(Pcm *);
PcmStatus pcm_spark_calculate(Pcm *);
#endif
