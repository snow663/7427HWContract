#ifndef PSEUDO_SOURCE_CONTROL_H
#define PSEUDO_SOURCE_CONTROL_H
#include "pcm.h"
PcmStatus pcm_common_io(Pcm *);
PcmStatus pcm_input_housekeeping(Pcm *);
PcmStatus pcm_spark_control(Pcm *);
PcmStatus pcm_egr_feedback(Pcm *);
PcmStatus pcm_egr_control(Pcm *);
PcmStatus pcm_serial_poll(Pcm *);
PcmStatus pcm_egr_flow(Pcm *);
PcmStatus pcm_transmission_input(Pcm *);
PcmStatus pcm_pressure_tcc(Pcm *);
PcmStatus pcm_fuel_control(Pcm *);
PcmStatus pcm_egr_output(Pcm *);
PcmStatus pcm_shift_control(Pcm *);
PcmStatus pcm_iac_control(Pcm *);
PcmStatus pcm_transmission_spark(Pcm *);
PcmStatus pcm_alternate_rpm(Pcm *);
PcmStatus pcm_iac_step(Pcm *);
PcmStatus pcm_adc_feedback(Pcm *);
PcmStatus pcm_current_control(Pcm *);
PcmStatus pcm_ac_switch_inputs(Pcm *);
PcmStatus pcm_transmission_outputs(Pcm *);
/* D4EB diagnostics, threshold selection and final gear arbitration. */
PcmStatus pcm_transmission_mask_scan(Pcm *, uint16_t table, bool *active);
PcmStatus pcm_transmission_fault_gate_684(Pcm *);
PcmStatus pcm_transmission_fault_gate_6ac(Pcm *);
PcmStatus pcm_transmission_fault_gate_69c(Pcm *);
PcmStatus pcm_transmission_d4eb_prefix(Pcm *);
PcmStatus pcm_transmission_gear_limit(Pcm *, uint8_t proposed, uint8_t *capped);
PcmStatus pcm_transmission_gear_finalize(Pcm *, uint8_t proposed);
PcmStatus pcm_transmission_threshold_select(Pcm *, uint16_t table, uint8_t slot,
                                            uint8_t *value, bool *valid);
PcmStatus pcm_transmission_descriptor(Pcm *, uint16_t table, uint8_t selector,
                                      uint8_t gear, uint16_t *address, bool *valid);
PcmStatus pcm_transmission_cold_offset(Pcm *, uint16_t base, uint16_t offset, uint16_t *result);
PcmStatus pcm_transmission_temperature_gain(Pcm *, uint16_t table, uint16_t input, uint16_t *result);
PcmStatus pcm_transmission_normal_threshold(Pcm *, uint16_t group, uint8_t gear, uint8_t *value, bool *valid);
PcmStatus pcm_transmission_kickdown_threshold(Pcm *, uint16_t group, uint8_t gear, uint8_t *value, bool *valid);
PcmStatus pcm_transmission_kickdown_rpm(Pcm *, uint16_t group, uint8_t gear, uint16_t *value);
PcmStatus pcm_transmission_gear_select(Pcm *);
PcmStatus pcm_connection_probe(Pcm *);
PcmStatus pcm_iac_background(Pcm *);
PcmStatus pcm_shift_lamp(Pcm *);
PcmStatus pcm_egr_demand(Pcm *);
PcmStatus pcm_vss_filter(Pcm *);
/* PR48 EGR, diagnostics and whole-slotF callable sources. */
PcmStatus pcm_transmission_baro(Pcm *);
PcmStatus pcm_tcc_nonelectronic(Pcm *);
PcmStatus pcm_fault_primary_reaction(Pcm *);
PcmStatus pcm_fault_injection_reaction(Pcm *);
PcmStatus pcm_fault_reaction_mask(Pcm *, uint16_t mask_base, uint8_t *value);
PcmStatus pcm_diagnostic_brake_set(Pcm *);
PcmStatus pcm_diagnostic_brake_clear(Pcm *);
PcmStatus pcm_diagnostic_tcc_slip(Pcm *);
PcmStatus pcm_diagnostic_top_gear_slip(Pcm *);
PcmStatus pcm_diagnostic_tcc_released_slip(Pcm *);
PcmStatus pcm_diagnostic_current_error(Pcm *);
PcmStatus pcm_diagnostic_transmission_temperature(Pcm *);
PcmStatus pcm_diagnostic_ratio_invalid(Pcm *);
PcmStatus pcm_diagnostic_ratio_lowgear(Pcm *);
PcmStatus pcm_diagnostic_ratio_highgear(Pcm *);
PcmStatus pcm_diagnostic_slot_f(Pcm *);

/* Resident slot 04 diagnostic and transmission entries. */
PcmStatus pcm_diagnostic_coolant_adc_low(Pcm *);
PcmStatus pcm_diagnostic_coolant_adc_high(Pcm *);
PcmStatus pcm_diagnostic_trans_temp_adc_low(Pcm *);
PcmStatus pcm_diagnostic_trans_temp_adc_high(Pcm *);
PcmStatus pcm_diagnostic_baro_adc_high(Pcm *);
PcmStatus pcm_diagnostic_baro_adc_low(Pcm *);
PcmStatus pcm_diagnostic_solenoid_81(Pcm *);
PcmStatus pcm_diagnostic_solenoid_82(Pcm *);
PcmStatus pcm_diagnostic_solenoid_83(Pcm *);
PcmStatus pcm_diagnostic_battery_52(Pcm *);
PcmStatus pcm_diagnostic_battery_53(Pcm *);
PcmStatus pcm_diagnostic_battery_compensated(Pcm *);
PcmStatus pcm_diagnostic_slot_04(Pcm *);
PcmStatus pcm_transmission_adaptive_reset(Pcm *);
PcmStatus pcm_transmission_adaptive_restore(Pcm *);
PcmStatus pcm_transmission_temperature_input(Pcm *);
PcmStatus pcm_transmission_temperature_filter(Pcm *);

/* A first real algorithm slice. Inputs retain the factory fixed-point
 * representations; they are not yet RPM/kPa/microsecond engineering units. */
typedef struct {
    uint16_t density, temperature, period, injector_flow;
    uint8_t volume, volumetric_efficiency, afr;
} PcmFuelBaseInputs;
typedef struct { uint16_t displaced, air, air_rate, mixture_quotient, pulse; } PcmFuelBase;
PcmFuelBase pcm_fuel_base(const PcmFuelBaseInputs *);
#endif
