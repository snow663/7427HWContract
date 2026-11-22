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
PcmStatus pcm_connection_probe(Pcm *);
PcmStatus pcm_iac_background(Pcm *);
PcmStatus pcm_shift_lamp(Pcm *);
PcmStatus pcm_egr_demand(Pcm *);
PcmStatus pcm_vss_filter(Pcm *);
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

/* A first real algorithm slice. Inputs retain the factory fixed-point
 * representations; they are not yet RPM/kPa/microsecond engineering units. */
typedef struct {
    uint16_t density, temperature, period, injector_flow;
    uint8_t volume, volumetric_efficiency, afr;
} PcmFuelBaseInputs;
typedef struct { uint16_t displaced, air, air_rate, mixture_quotient, pulse; } PcmFuelBase;
PcmFuelBase pcm_fuel_base(const PcmFuelBaseInputs *);
#endif
