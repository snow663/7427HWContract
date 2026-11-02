#include "fuel.h"
#include "mixture_internal.h"
#include "hardware.h"
#include "reference_math.h"
/* 858B..85B1. The period multiplier is the low byte of32*4141. */
PcmStatus pcm_fuel_crank_coordinate(Pcm *pcm, uint8_t *coordinate)
{
    if (coordinate == NULL) return PCM_BAD_CONFIGURATION;
    uint16_t period;
    PcmStatus result = pcm_read16(pcm, PCM_REFERENCE_PERIOD, &period);
    if (result != PCM_OK) return result;
    MIX_CAL();
    uint8_t scale = (uint8_t)(32u * cal->period_scale);
    if (scale != 0) period = pcm_gain_word(period, scale);
    uint16_t quotient = period == 0 ? 0 : mix_fraction(614, period);
    *coordinate = mix_min((uint8_t)(quotient >> 8), 127);
    return PCM_OK;
}
