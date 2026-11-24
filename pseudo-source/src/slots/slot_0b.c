#include "scheduler.h"
#include "control.h"
#include "../system/system_internal.h"

/* $7B3D: $D4EB -> $C514. The $F5CF marker belongs to slot 03. */
PcmStatus pcm_slot_0b(Pcm *pcm)
{
    if (pcm == NULL || pcm->platform == NULL) return PCM_BAD_CONFIGURATION;
    SYS_RUN(pcm_transmission_gear_select(pcm));
    return pcm_transmission_outputs(pcm);
}
