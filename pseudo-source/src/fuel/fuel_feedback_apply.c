#include "fuel.h"
#include "feedback_internal.h"
#include "hardware.h"
/*8380..83B0. Signed INT/P addition, MAP AE addition, then running packet. */
PcmStatus pcm_fuel_feedback_apply(Pcm *pcm)
{
    uint8_t encoded = pcm->fuel.feedback_encoded;
    if (encoded<128) pcm->fuel.corrected_pulse=mix_word((uint32_t)pcm->fuel.corrected_pulse+encoded);
    else {
        uint8_t magnitude=(uint8_t)(0u-encoded);
        pcm->fuel.corrected_pulse=pcm->fuel.corrected_pulse>magnitude ? (uint16_t)(pcm->fuel.corrected_pulse-magnitude) : 0;
    }
    pcm->fuel.corrected_pulse=mix_word((uint32_t)pcm->fuel.corrected_pulse+pcm->fuel.map_ae);
    pcm->reference.running_packet=pcm->fuel.corrected_pulse;
    return PCM_OK;
}
