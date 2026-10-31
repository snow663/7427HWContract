#include "reference_math.h"
/* F499..F4A3 ->F4BD..F4DD: cap input, use offset0 and rounded interpolation. */
PcmStatus pcm_lookup_capped(uint8_t input, const PcmCappedCurve *curve, uint8_t *result)
{
    if (curve == NULL || curve->values == NULL || result == NULL) return PCM_BAD_CONFIGURATION;
    if (input > curve->limit) input = curve->limit;
    if ((input >> 4) + 1u >= curve->length) return PCM_BAD_CONFIGURATION;
    *result = pcm_lookup16(input, curve->values);
    return PCM_OK;
}
