#include "fuel.h"
#include "feedback_internal.h"
#include "hardware.h"
/*8342..837F. Fourfold BARO correction precedes the separate battery gain. */
PcmStatus pcm_fuel_baro_battery(Pcm *pcm)
{
    FB_CAL();
    uint8_t coordinate = (uint8_t)(((uint16_t)mix_min(pcm->spark.map_filtered,216)*151u+145u)>>8), gain;
    FB_RUN(pcm_lookup2d(coordinate,pcm->spark.barometric_pressure,&cal->baro,&gain));
    pcm->fuel.corrected_pulse = mix_word(4u*pcm_gain_word(pcm->fuel.corrected_pulse,gain));
    return pcm_fuel_pulse_scale(pcm,pcm_lookup16(pcm->reference.battery,cal->battery));
}
