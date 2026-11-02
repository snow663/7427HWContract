#include "fuel.h"
#include "feedback_internal.h"
#include "hardware.h"
/*8032..8057. EGR gain rounds its word with wrap; PE suppresses learned lean. */
PcmStatus pcm_fuel_egr_blm(Pcm *pcm)
{
    uint16_t fraction = (uint16_t)((uint16_t)pcm->spark.egr_fraction_high*256u+pcm->fuel.egr_fraction_low);
    uint8_t gain = (uint8_t)((uint16_t)(fraction+128u)>>8);
    pcm->fuel.egr_subtract = (uint16_t)(pcm_gain_word(pcm->fuel.corrected_pulse,gain)>>2);
    pcm->fuel.corrected_pulse = (uint16_t)(pcm->fuel.corrected_pulse-pcm->fuel.egr_subtract);
    uint8_t blm = pcm->iac.blm_value;
    if (blm>=128 || !pcm->runtime.power_enrichment) return pcm_fuel_blm_scale(pcm,blm);
    return PCM_OK;
}
