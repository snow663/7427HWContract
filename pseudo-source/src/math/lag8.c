#include "reference_math.h"
/* F459..F478. Floor signed division explicitly; C's negative division truncates
 * toward zero, while the factory filter retains its asymmetric rounding. */
uint16_t pcm_lag8(uint8_t target, uint16_t old, uint8_t gain)
{
    int32_t numerator = ((int32_t)target * 256 - old) * gain + 128;
    int32_t step = numerator >= 0 ? numerator / 256 : -((-numerator + 255) / 256);
    return (uint16_t)((int32_t)old + step);
}
