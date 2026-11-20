#include "scheduler.h"
#include "control.h"
/* BMHM $7ABD..$7AC6, actual source call order:
 * F5CF: optional $1806 heads-up stage, then $F7 -> $0F00 publication.
 * D4EB: multiple auto-trans gear/speed helpers; remains an actual source
 * boundary until the entire transitive path is reconstructed.
 * C514: resident transmission-output controller, called after D4EB.
 *
 * Default behavior continues to defer to PCM_SLOT_03. Only an explicit
 * source-mode opt-in enables this partial resident sequence, never
 * silently treats unavailable external machine code as a no-op. */
PcmStatus pcm_slot_03(Pcm *pcm)
{
    if(pcm==NULL||pcm->platform==NULL)return PCM_BAD_CONFIGURATION;
    if(!pcm->platform->enable_resident_slow_slots)
        return pcm_run_task(pcm,PCM_SLOT_03);
    uint8_t flags;
    PcmStatus status=pcm_read8(pcm,0x0086u,&flags);
    if(status!=PCM_OK)return status;
    if(flags&0x40u) {
        if(pcm->platform->call_address==NULL) {
            pcm->unresolved_task=PCM_SLOT_03;return PCM_UNIMPLEMENTED;
        }
        status=pcm->platform->call_address(pcm->platform->context,0x1806u);
        if(status!=PCM_OK)return status;
    }
    status=pcm_write8(pcm,0x0f00u,247u);
    if(status!=PCM_OK)return status;
    if(pcm->platform->call_address==NULL) {
        pcm->unresolved_task=PCM_SLOT_03;return PCM_UNIMPLEMENTED;
    }
    status=pcm->platform->call_address(pcm->platform->context,0xd4ebu);
    if(status!=PCM_OK)return status;
    return pcm_transmission_outputs(pcm);
}
