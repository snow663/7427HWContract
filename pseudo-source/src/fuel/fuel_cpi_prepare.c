#include "fuel.h"
#include "delivery_internal.h"
#include "hardware.h"
/*83C4..83FA. Entry D is PW; the qualifying path reloads it after CLI. */
PcmStatus pcm_fuel_cpi_prepare(Pcm *pcm)
{
    if (!pcm->reference.packet_updated) {
        DL_RUN(pcm_mask_irq(pcm,true));
        if (pcm->reference.split_clear!=255) ++pcm->reference.split_clear;
        DL_RUN(pcm_mask_irq(pcm,false));
        DL_CAL();
        if (pcm->reference.running_packet>cal->sync_threshold[0] || pcm->reference.split_clear<cal->cpi_delay) return PCM_OK;
        pcm->reference.packet_updated=true;pcm->reference.extra_guard=true;
    }
    pcm->fuel.corrected_pulse=mix_word(2u*pcm->fuel.corrected_pulse);
    return PCM_OK;
}
