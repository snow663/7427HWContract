#include "spark.h"
/* A6BE..A6D9: exact piecewise raw-period transform after previous-period save. */
uint16_t pcm_spark_reference_term(uint16_t period)
{
    if (period < 458u) return (uint16_t)((period >> 1) + 79u);
    if (period < 1638u) return (uint16_t)(((period - 458u) >> 4) + 308u);
    return (uint16_t)(((period - 458u) >> 2) + 87u);
}
