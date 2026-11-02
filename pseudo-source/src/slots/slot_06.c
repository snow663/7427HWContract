#include "scheduler.h"
#include "control.h"
#include "knock.h"
/* 7B14..7B1A: resident CB15 inputs precede resident CE10 learning. */
PcmStatus pcm_slot_06(Pcm *pcm)
{
    PcmStatus result = pcm_ac_switch_inputs(pcm);
    if (result != PCM_OK) return result;
    return pcm_low_octane_learn(pcm);
}
