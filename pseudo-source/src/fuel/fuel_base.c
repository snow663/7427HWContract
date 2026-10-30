#include "control.h"
static uint16_t fraction(uint16_t n, uint16_t d)
{
    return d == 0 || n >= d ? UINT16_MAX : (uint16_t)(((uint32_t)n << 16) / d);
}
static uint16_t multiply(uint8_t coefficient, uint16_t value)
{
    return (uint16_t)(((uint32_t)coefficient * value + 128u) >> 8);
}
static uint16_t cap16(uint32_t value)
{
    return value > UINT16_MAX ? UINT16_MAX : (uint16_t)value;
}
/* Reference 7FD8..802F; each divide retains its own truncation/saturation. */
PcmFuelBase pcm_fuel_base(const PcmFuelBaseInputs *in)
{
    PcmFuelBase out;
    out.displaced = multiply(in->volume, fraction(in->density, in->temperature));
    out.air = multiply(in->volumetric_efficiency, out.displaced);
    out.air_rate = in->period ? cap16(2u * (((uint32_t)out.air << 8) / in->period)) : UINT16_MAX;
    out.mixture_quotient = fraction((uint16_t)(out.air >> 2), (uint16_t)((uint16_t)in->afr << 8));
    out.pulse = in->injector_flow ? cap16(((uint32_t)out.mixture_quotient << 8) / in->injector_flow) : UINT16_MAX;
    return out;
}
