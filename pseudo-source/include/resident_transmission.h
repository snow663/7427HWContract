#ifndef PCM_RESIDENT_TRANSMISSION_H
#define PCM_RESIDENT_TRANSMISSION_H
#include "pcm.h"
/* Logical raw-address providers must maintain canonical shared state. */
PcmStatus pcm_resident_gear_ratio(Pcm *, uint16_t *);
PcmStatus pcm_resident_speed_ratio(Pcm *);
PcmStatus pcm_resident_temperature_class(Pcm *);
PcmStatus pcm_resident_fault_e5cf(Pcm *);
PcmStatus pcm_resident_fault_e5f1(Pcm *);
PcmStatus pcm_resident_fault_e60b(Pcm *);
PcmStatus pcm_resident_fault_e6f5(Pcm *);
PcmStatus pcm_resident_diag_e7c7(Pcm *);
PcmStatus pcm_resident_diag_e808(Pcm *);
PcmStatus pcm_resident_diag_e847(Pcm *);
PcmStatus pcm_resident_diag_e8c8(Pcm *);
PcmStatus pcm_resident_diag_eb81(Pcm *);
PcmStatus pcm_resident_diag_ebc0(Pcm *);
PcmStatus pcm_resident_diag_eccc(Pcm *);
PcmStatus pcm_resident_diag_ef2b(Pcm *);
PcmStatus pcm_resident_input_aea4(Pcm *);
PcmStatus pcm_resident_input_b018(Pcm *);
PcmStatus pcm_resident_input_b089(Pcm *);
PcmStatus pcm_resident_input_b1f0(Pcm *);
PcmStatus pcm_resident_input_b23c(Pcm *);
PcmStatus pcm_resident_input_c483(Pcm *);
PcmStatus pcm_resident_capture_e58c(Pcm *,uint16_t,uint16_t,uint8_t,uint16_t *);
PcmStatus pcm_resident_lag_f420(Pcm *,uint16_t,uint16_t,uint16_t,uint16_t *);
uint16_t pcm_resident_mul_f5a2(uint16_t,uint16_t);
PcmStatus pcm_transmission_input_resident(Pcm *);
#endif
