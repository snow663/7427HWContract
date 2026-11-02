#include "fuel.h"
#include "feedback_internal.h"
#include "hardware.h"
/*82ED..8341. Publish the raw derivative before upper/lower factor selection. */
PcmStatus pcm_fuel_derivative_correction(Pcm *pcm)
{
    FB_CAL();
    if (pcm->reference.load_coordinate < cal->derivative_load || pcm->reference.throttle > cal->derivative_throttle ||
        pcm->spark.vehicle_speed_high > cal->derivative_speed || pcm->reference.coolant < cal->derivative_coolant) {
        pcm->spark.idle_derivative = 128;return PCM_OK;
    }
    uint8_t value = mix_byte(((uint32_t)mix_fraction((uint16_t)(pcm->reference.load_event>>1),pcm->reference.load_filtered)+128u)>>8);
    pcm->spark.idle_derivative = value;
    if (value>=cal->derivative_bounds[1]) value=cal->derivative_bounds[1];
    else if (value<cal->derivative_bounds[0]) value=cal->derivative_bounds[0];
    pcm->fuel.corrected_pulse = mix_word(2u*pcm_gain_word(pcm->fuel.corrected_pulse,value));
    return PCM_OK;
}
