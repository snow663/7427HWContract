#include "scheduler.h"
#include "knock.h"
/* 7B2B calls CEBB..CF15 then returns. This slot has no other task body. */
PcmStatus pcm_slot_08(Pcm *pcm)
{
    PcmStatus result = pcm_knock_decay(pcm);
    if (result != PCM_OK) return result;
    return pcm_knock_sensor(pcm);
}
