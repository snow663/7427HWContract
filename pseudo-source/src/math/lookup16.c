#include "reference_math.h"
/* F4C1..F4DD: 16 segments, rounded absolute difference, either slope. */
uint8_t pcm_lookup16(uint8_t input, const uint8_t *knots)
{
    uint8_t index = (uint8_t)(input >> 4), fraction = (uint8_t)(input << 4);
    uint8_t first = knots[index], second = knots[index + 1u];
    uint8_t difference = first > second ? (uint8_t)(first - second) : (uint8_t)(second - first);
    uint8_t step = (uint8_t)(((uint16_t)difference * fraction + 128u) >> 8);
    return first > second ? (uint8_t)(first - step) : (uint8_t)(first + step);
}
