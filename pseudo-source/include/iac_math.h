#ifndef PSEUDO_SOURCE_IAC_MATH_H
#define PSEUDO_SOURCE_IAC_MATH_H
#include <stdint.h>
/* Private arithmetic shared by the resident IAC routines. */
static inline uint16_t iac_cap(uint32_t value)
{ return value > UINT16_MAX ? UINT16_MAX : (uint16_t)value; }
static inline uint16_t iac_add_high(uint16_t word, uint8_t value)
{ return iac_cap((uint32_t)word + ((uint32_t)value << 8)); }
static inline uint16_t iac_sub_high(uint16_t word, uint8_t value)
{ return (word >> 8) < value ? 0 : (uint16_t)(word - ((uint16_t)value << 8)); }
static inline uint8_t iac_error_coordinate(uint8_t error)
{
    if (error > 40u) return 160;
    if (error > 16u) return (uint8_t)(2u * error + 80u);
    if (error > 4u) return (uint8_t)(4u * error + 48u);
    return (uint8_t)(16u * error);
}
#endif
