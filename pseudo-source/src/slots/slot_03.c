#include "scheduler.h"
#include "control.h"
#include "../system/system_internal.h"

/* $7ABD: $F5CF -> $D4EB -> $C514. The only external body is the
 * optional $1806 module selected by $0086.6 before the marker write. */
PcmStatus pcm_slot_03(Pcm *pcm)
{
    if (pcm == NULL || pcm->platform == NULL) return PCM_BAD_CONFIGURATION;
    uint8_t flags;
    SYS_RUN(pcm_read8(pcm, 0x0086, &flags));
    if (flags & 0x40u) {
        if (pcm->platform->call_address == NULL) {
            pcm->unresolved_task = PCM_SLOT_03;
            return PCM_UNIMPLEMENTED;
        }
        SYS_RUN(pcm->platform->call_address(pcm->platform->context, 0x1806));
    }
    SYS_RUN(pcm_write8(pcm, 0x0f00, 0xf7));
    SYS_RUN(pcm_transmission_gear_select(pcm));
    return pcm_transmission_outputs(pcm);
}
