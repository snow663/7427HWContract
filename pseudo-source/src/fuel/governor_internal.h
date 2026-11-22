#ifndef PCM_GOVERNOR_INTERNAL_H
#define PCM_GOVERNOR_INTERNAL_H
#include "fuel.h"
#include "../system/system_internal.h"
static inline uint16_t gov_product(uint8_t a,uint8_t b,unsigned shift)
{
    uint32_t value=(uint32_t)a*b*((uint32_t)1u<<shift);
    return value>65535u?65535:(uint16_t)value;
}
/* F4B6: scale byte, captured knot pair, then fresh base byte. */
static inline PcmStatus gov_scaled(Pcm *pcm,uint8_t input,uint16_t table,uint8_t *out)
{
    uint8_t scale,base;uint16_t knots;SYS_RUN(pcm_read8(pcm,table,&scale));
    uint16_t coordinate=(uint16_t)((uint16_t)input*scale);
    uint16_t address=(uint16_t)(table+1u+(coordinate>>8));
    SYS_RUN(pcm_read16(pcm,address,&knots));SYS_RUN(pcm_read8(pcm,address,&base));
    uint8_t first=(uint8_t)(knots>>8),second=(uint8_t)knots;
    uint8_t difference=first>second?(uint8_t)(first-second):(uint8_t)(second-first);
    uint8_t step=(uint8_t)(((uint16_t)difference*(uint8_t)coordinate+128u)>>8);
    *out=first>=second?(uint8_t)(base-step):(uint8_t)(base+step);return PCM_OK;
}
static inline PcmStatus gov_capped(Pcm *pcm,uint8_t input,uint16_t table,uint8_t *out)
{
    uint8_t limit;SYS_RUN(pcm_read8(pcm,table,&limit));
    if (input>limit) SYS_RUN(pcm_read8(pcm,table,&input));
    return sys_curve16(pcm,input,(uint16_t)(table+1u),out);
}
/* F550 samples the low byte first, then the high byte. */
static inline PcmStatus gov_gain_word(Pcm *pcm,uint16_t address,uint8_t gain,uint16_t *out)
{
    uint8_t low,high;SYS_RUN(pcm_read8(pcm,(uint16_t)(address+1u),&low));
    SYS_RUN(pcm_read8(pcm,address,&high));
    *out=(uint16_t)((uint16_t)high*gain+(((uint16_t)low*gain+128u)>>8));return PCM_OK;
}
/* Preserve separate comparison and replacement reads of a byte floor. */
static inline PcmStatus gov_floor(Pcm *pcm,uint8_t value,bool borrowed,uint16_t address,uint8_t *out,bool *clamped)
{
    uint8_t minimum;
    if (!borrowed) {
        SYS_RUN(pcm_read8(pcm,address,&minimum));
        if (value>=minimum) { *out=value;*clamped=false;return PCM_OK; }
    }
    SYS_RUN(pcm_read8(pcm,address,out));*clamped=true;return PCM_OK;
}
#endif
