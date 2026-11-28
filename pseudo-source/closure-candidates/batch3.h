#ifndef PCM_CLOSURE_BATCH3_H
#define PCM_CLOSURE_BATCH3_H
#include "pcm.h"
PcmStatus closure_input_aea4(Pcm *);
PcmStatus closure_input_b018(Pcm *);
PcmStatus closure_input_b089(Pcm *);
PcmStatus closure_input_b1f0(Pcm *);
PcmStatus closure_input_b23c(Pcm *);
PcmStatus closure_input_c483(Pcm *);
PcmStatus closure_capture_e58c(Pcm *,uint16_t,uint16_t,uint8_t,uint16_t *);
PcmStatus closure_lag_f420(Pcm *,uint16_t,uint16_t,uint16_t,uint16_t *);
uint16_t closure_mul_f5a2(uint16_t,uint16_t);
PcmStatus closure_input_prefix(Pcm *);
#endif
