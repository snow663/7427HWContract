#include "board_io.h"
#include "hardware.h"
#define RUN(call) do { PcmStatus result=(call);if (result!=PCM_OK) return result; } while (0)
/* 7BF5..7C0E. The status stays latched in A across CLI; the saved0073.6
 * flag remains the existing REF owner rather than a second independent copy. */
PcmStatus pcm_vss_sample(Pcm *pcm)
{
    RUN(pcm_mask_irq(pcm,true));
    uint16_t status;
    RUN(pcm_read16(pcm,PCM_REFERENCE_STATUS,&status));
    pcm->io.status_context=status&0xbfffu;
    pcm->reference.extra_request=(status&0x4000u)!=0;
    RUN(pcm_mask_irq(pcm,false));
    if (status&0x0400u) {
        uint16_t timestamp;
        RUN(pcm_read16(pcm,PCM_VSS_TIMESTAMP,&timestamp));
        if (timestamp!=pcm->io.vss_timestamp) {
            ++pcm->io.vss_changes;
            pcm->io.vss_timestamp=timestamp;
        }
    }
    return PCM_OK;
}
