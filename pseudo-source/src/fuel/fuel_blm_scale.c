#include "fuel.h"
#include "feedback_internal.h"
#include "hardware.h"
/*80EE..8105. Store the saturated double before applying the BLM gain. */
PcmStatus pcm_fuel_blm_scale(Pcm *pcm, uint8_t gain)
{
    pcm->fuel.corrected_pulse = mix_word(2u*pcm->fuel.corrected_pulse);
    return pcm_fuel_pulse_scale(pcm,gain);
}
