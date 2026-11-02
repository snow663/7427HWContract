#include "fuel.h"
/*7E40..7E4E. The zero-extended MAP byte is always below the fixed FDIV divisor. */
PcmStatus pcm_fuel_density(Pcm *pcm)
{
    pcm->spark.density = (uint16_t)(((uint32_t)pcm->spark.map_filtered * 65536u) / 694u + 2649u);
    return PCM_OK;
}
