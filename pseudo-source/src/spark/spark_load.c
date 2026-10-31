#include "spark.h"
static uint8_t scaled(uint8_t input)
{
    uint32_t value = ((uint32_t)151u * input + 64u) * 2u;
    return value > 65535u ? 255u : (uint8_t)(value >> 8);
}
/* A466..A4B2: three distinct load coordinates; FDIV overflow yields FFFF. */
PcmStatus pcm_spark_load(Pcm *pcm)
{
    uint8_t baro = pcm->spark.barometric_high;
    uint8_t map = pcm->spark.map_filtered;
    uint8_t delta = baro > map ? (uint8_t)(baro - map) : 1u;
    pcm->spark.vacuum = (uint8_t)(0u - scaled(delta));
    map = pcm->spark.map_filtered;
    pcm->spark.load_coordinate = scaled(map >= 26u ? (uint8_t)(map - 26u) : 0u);
    uint16_t divisor = (uint16_t)((uint16_t)pcm->spark.normalized_load_divisor << 8);
    uint16_t numerator = pcm->spark.density;
    uint16_t quotient = divisor == 0 || numerator >= divisor ? UINT16_MAX :
        (uint16_t)(((uint32_t)numerator << 16) / divisor);
    uint32_t value = quotient >= 8192u ? (uint32_t)(quotient - 8192u) * 2u : 0u;
    pcm->spark.normalized_load = value > 65535u ? 255u : (uint8_t)(value >> 8);
    return PCM_OK;
}
