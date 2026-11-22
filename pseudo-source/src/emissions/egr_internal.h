#ifndef PCM_EGR_INTERNAL_H
#define PCM_EGR_INTERNAL_H
#include "control.h"
#include "../system/system_internal.h"
/* F4B6 scaled entry: sample the scale, capture adjacent knots as one word,
 * then reread the base knot after the rounded interpolation. */
static inline PcmStatus egr_scaled(Pcm *pcm,uint8_t input,uint16_t header,uint8_t *out)
{
    uint8_t scale,base;uint16_t knots;SYS_RUN(pcm_read8(pcm,header,&scale));
    uint16_t coordinate=(uint16_t)((uint16_t)input*scale);
    uint16_t address=(uint16_t)(header+1u+(coordinate>>8));
    SYS_RUN(pcm_read16(pcm,address,&knots));
    uint8_t first=(uint8_t)(knots>>8),second=(uint8_t)knots;
    uint8_t difference=first>second?(uint8_t)(first-second):(uint8_t)(second-first);
    uint8_t step=(uint8_t)(((uint16_t)difference*(uint8_t)coordinate+128u)>>8);
    SYS_RUN(pcm_read8(pcm,address,&base));
    *out=first>=second?(uint8_t)(base-step):(uint8_t)(base+step);
    return PCM_OK;
}
static inline uint16_t egr_combine(uint16_t base,uint16_t adjustment,bool subtract)
{
    if (subtract) return base<adjustment?0:(uint16_t)(base-adjustment);
    uint32_t sum=(uint32_t)base+adjustment;return sum>65535u?65535:(uint16_t)sum;
}
#endif
