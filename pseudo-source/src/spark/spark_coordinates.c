#include "spark.h"
/* A5FE..A628 and AC71..AC9A: divisor double wraps before FDIV; the two
 * coordinates have different transforms and both saturate at their top edge. */
uint16_t pcm_spark_coordinates(uint16_t basis, uint8_t *low, uint8_t *rounded)
{
    uint16_t divisor = (uint16_t)(basis * 2u);
    uint16_t rpm = divisor <= 307u ? UINT16_MAX : (uint16_t)((307UL << 16) / divisor);
    uint8_t low_value;
    if (rpm >= 0x6000u) {
        uint32_t value = (uint32_t)rpm + 0x4080u;
        low_value = value > 65535u ? 255u : (uint8_t)(value >> 8);
    } else {
        uint32_t value = (uint32_t)rpm * 2u;
        low_value = value < 0x1f80u ? 0u : (uint8_t)((value - 0x1f80u) >> 8);
    }
    uint16_t value = (uint16_t)(((uint32_t)rpm + 128u) >> 8);
    if (low != NULL) *low = low_value;
    if (rounded != NULL) *rounded = value > 255u ? 255u : (uint8_t)value;
    return rpm;
}
