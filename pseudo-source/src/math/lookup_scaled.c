#include "reference_math.h"
/* F4B6..F4BB ->F4C5..F4DD: input*scale supplies index and fraction. */
PcmStatus pcm_lookup_scaled(uint8_t input, const PcmScaledCurve *curve, uint8_t *result)
{
    if (curve == NULL || curve->values == NULL || result == NULL) return PCM_BAD_CONFIGURATION;
    uint16_t coordinate = (uint16_t)input * curve->scale;
    unsigned index = coordinate >> 8;
    if (index + 1u >= curve->length) return PCM_BAD_CONFIGURATION;
    uint8_t first = curve->values[index], second = curve->values[index + 1u];
    uint8_t difference = first > second ? (uint8_t)(first - second) : (uint8_t)(second - first);
    uint8_t step = (uint8_t)(((uint16_t)difference * (uint8_t)coordinate + 128u) >> 8);
    *result = first > second ? (uint8_t)(first - step) : (uint8_t)(first + step);
    return PCM_OK;
}
