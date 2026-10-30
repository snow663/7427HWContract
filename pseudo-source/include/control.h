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

/* A first real algorithm slice. Inputs retain the factory fixed-point
 * representations; they are not yet RPM/kPa/microsecond engineering units. */
typedef struct {
    uint16_t density, temperature, period, injector_flow;
    uint8_t volume, volumetric_efficiency, afr;
} PcmFuelBaseInputs;
typedef struct { uint16_t displaced, air, air_rate, mixture_quotient, pulse; } PcmFuelBase;
PcmFuelBase pcm_fuel_base(const PcmFuelBaseInputs *);
#endif
