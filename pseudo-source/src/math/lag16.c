#include "reference_math.h"
/* F436..F458 and F479..F498. Borrow selects a signed17-bit difference;
 * the low product's MUL carry supplies rounding. Preserve both word wraps. */
uint16_t pcm_lag16(uint16_t target, uint16_t old, uint8_t gain, uint16_t *intermediate)
{
    uint16_t difference = (uint16_t)(target - old);
    int32_t high = difference >> 8;
    if (target < old) high -= 256;
    uint16_t partial = (uint16_t)((int32_t)old + high * gain);
    if (intermediate != NULL) *intermediate = partial;
    return (uint16_t)(partial + (((difference & 255u) * gain + 128u) >> 8));
}
