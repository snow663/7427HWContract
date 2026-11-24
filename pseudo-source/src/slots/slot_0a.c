#include "scheduler.h"
#include "control.h"

/* 7B39..7B3C. The phase-bit hold is inside D2B2. */
PcmStatus pcm_slot_0a(Pcm *pcm)
{
    return pcm_canister_purge(pcm);
}
