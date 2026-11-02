#include "reference_math.h"
/* F4A4..F4B4 -> F4B8: lower-offset floor, upper cap, scaled lookup. */
PcmStatus pcm_lookup_offset(uint8_t input, const PcmOffsetCurve *curve, uint8_t *result)
{
    if (curve == NULL) return PCM_BAD_CONFIGURATION;
    uint8_t coordinate = input < curve->offset ? 0 : (uint8_t)(input - curve->offset);
    if (coordinate > curve->limit) coordinate = curve->limit;
    return pcm_lookup_scaled(coordinate, &curve->curve, result);
}
