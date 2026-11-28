#include "resident_input_private_3.h"

/* F5A2: four byte products assemble the high word, no rounding. */
uint16_t pcm_resident_mul_f5a2(uint16_t d,uint16_t x)
{
    return (uint16_t)(((uint32_t)d*x)>>16);
}
