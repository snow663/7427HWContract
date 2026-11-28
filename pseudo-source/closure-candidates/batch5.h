#ifndef PCM_CLOSURE_BATCH5_H
#define PCM_CLOSURE_BATCH5_H
#include "pcm.h"
typedef struct {
    uint16_t stack_pointer, register_base, next_pc;
    uint8_t ccr;
} ClosureResetState;
PcmStatus closure_reset_prelude(Pcm *,ClosureResetState *);
PcmStatus closure_reset_task(Pcm *,PcmTask);
PcmStatus closure_reset_boot(Pcm *,const PcmPlatform *,const PcmCalibration *);
PcmStatus closure_input_joined(Pcm *);
#endif
