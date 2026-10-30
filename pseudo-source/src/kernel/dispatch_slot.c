#include "scheduler.h"
/* Reference 7A44..7AA5. Addresses become linker-assigned C function pointers. */
PcmStatus pcm_dispatch_slot(Pcm *pcm)
{
    static const PcmRoutine slots[16] = {
        pcm_slot_00, pcm_slot_01, pcm_slot_02, pcm_slot_03,
        pcm_slot_04, pcm_slot_05, pcm_slot_06, pcm_slot_07,
        pcm_slot_08, pcm_slot_09, pcm_slot_0a, pcm_slot_0b,
        pcm_slot_0c, pcm_slot_0d, pcm_slot_0e, pcm_slot_0f
    };
    return slots[pcm->scheduler.phase & 15u](pcm);
}
