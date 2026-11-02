#include "fuel.h"
#include "feedback_internal.h"
#include "hardware.h"
/*80FC..8105. Decel multiplier entry without the BLM pre-double. */
PcmStatus pcm_fuel_pulse_scale(Pcm *pcm, uint8_t gain)
{
    pcm->fuel.corrected_pulse = pcm_gain_word(pcm->fuel.corrected_pulse,gain);
    return PCM_OK;
}
