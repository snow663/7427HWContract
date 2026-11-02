#include "scheduler.h"
#include "control.h"
#include "iac.h"
/* Reference 7B2F, table word 7A97.
 * Stock body: 7B2F:CF16;7B32:A2B0;7B35:D4DA
 * Keep EGR and VSS producers explicit around the resident slow IAC. */
PcmStatus pcm_slot_09(Pcm *pcm)
{
    PcmStatus result = pcm_egr_demand(pcm);
    if (result != PCM_OK) return result;
    result = pcm_iac_slow(pcm);
    if (result != PCM_OK) return result;
    return pcm_vss_filter(pcm);
}
