#ifndef PCM_CLOSURE_BATCH4_H
#define PCM_CLOSURE_BATCH4_H
#include "pcm.h"
PcmStatus closure_pressure_shape(Pcm *,uint16_t *);
PcmStatus closure_pressure_main(Pcm *);
PcmStatus closure_tcc_command(Pcm *);
PcmStatus closure_pressure_group(Pcm *);
#endif
