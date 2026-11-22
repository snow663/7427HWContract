#ifndef PCM_EGR_INTERNAL_H
#define PCM_EGR_INTERNAL_H
#include "control.h"
#include "../system/system_internal.h"
/* The captured slope/fraction and fresh base read are separate source values. */
static inline uint8_t egr_interpolate(uint8_t first,uint8_t second,uint8_t fraction,uint8_t base)
{
    uint8_t difference=first>second?(uint8_t)(first-second):(uint8_t)(second-first);
    uint8_t step=(uint8_t)(((uint16_t)difference*fraction+128u)>>8);
    return first>=second?(uint8_t)(base-step):(uint8_t)(base+step);
}
static inline PcmStatus egr_pair(Pcm *pcm,uint16_t address,uint8_t fraction,uint8_t *out)
{
    uint16_t knots;uint8_t base;SYS_RUN(pcm_read16(pcm,address,&knots));
    SYS_RUN(pcm_read8(pcm,address,&base));
    *out=egr_interpolate((uint8_t)(knots>>8),(uint8_t)knots,fraction,base);return PCM_OK;
}
/* F4DE: column interpolation below, then above, then row interpolation.
 * The row-index/stride product wraps to a byte before ABX. The stride is
 * sampled again before forming the second row address. */
static inline PcmStatus egr_surface(Pcm *pcm,uint8_t row,uint8_t column,uint16_t header,uint8_t *out)
{
    uint8_t offset,stride,below,above;SYS_RUN(pcm_read8(pcm,header,&offset));
    row=row<offset?0:(uint8_t)(row-offset);
    SYS_RUN(pcm_read8(pcm,(uint16_t)(header+1u),&offset));
    column=column<offset?0:(uint8_t)(column-offset);
    SYS_RUN(pcm_read8(pcm,(uint16_t)(header+2u),&stride));
    uint16_t first=(uint16_t)(header+(column>>4)+(uint8_t)((row>>4)*stride));
    SYS_RUN(pcm_read8(pcm,(uint16_t)(header+2u),&stride));
    SYS_RUN(egr_pair(pcm,(uint16_t)(first+stride+3u),(uint8_t)(column<<4),&below));
    SYS_RUN(egr_pair(pcm,(uint16_t)(first+3u),(uint8_t)(column<<4),&above));
    *out=egr_interpolate(above,below,(uint8_t)(row<<4),above);return PCM_OK;
}
/* MUL/ASLD retains the doubled product high byte; overflow selects FF. */
static inline uint8_t egr_double_product(uint8_t a,uint8_t b)
{
    uint16_t product=(uint16_t)((uint16_t)a*b);
    return product>32767u?255:(uint8_t)(product>>7);
}
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
