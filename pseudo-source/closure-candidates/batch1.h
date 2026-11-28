#ifndef PCM_CLOSURE_BATCH1_H
#define PCM_CLOSURE_BATCH1_H
#include "pcm.h"
PcmStatus closure_gear_ratio(Pcm *, uint16_t *);
PcmStatus closure_speed_ratio(Pcm *);
PcmStatus closure_temperature_class(Pcm *);
PcmStatus closure_fault_e5cf(Pcm *);
PcmStatus closure_fault_e5f1(Pcm *);
PcmStatus closure_fault_e60b(Pcm *);
PcmStatus closure_fault_e6f5(Pcm *);
#endif
