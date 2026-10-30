#include "reference_math.h"
/* F550..F563: multiply a word by an unsigned gain/256, retaining rounding. */
uint16_t pcm_gain_word(uint16_t word, uint8_t gain)
{
    return (uint16_t)(((uint32_t)word * gain + 128u) >> 8);
}
