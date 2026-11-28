#ifndef PCM_RESIDENT_INPUT_PRIVATE_3
#define PCM_RESIDENT_INPUT_PRIVATE_3
#include "resident_transmission.h"
#include "reference_math.h"
#include "../system/system_internal.h"
static inline uint16_t q(uint16_t d,uint16_t x)
{
    return x && d<x ? (uint16_t)(((uint32_t)d<<16)/x) : UINT16_MAX;
}

static inline uint16_t double_sat(uint16_t d)
{
    return d>0x7fffu ? UINT16_MAX : (uint16_t)(d<<1);
}

static inline uint16_t clamp_difference(uint16_t a,uint16_t b)
{
    int32_t d=(int32_t)a-b;
    if(d>32767) return 0x7fff;
    if(d< -32768) return 0x8000;
    return (uint16_t)d;
}

static inline PcmStatus test(Pcm *pcm,uint16_t a,uint8_t mask,bool *set)
{
    uint8_t v;
    SYS_RUN(pcm_read8(pcm,a,&v));
    *set=(v&mask)!=0;
    return PCM_OK;
}

static inline PcmStatus lag_store(Pcm *pcm,uint16_t source,uint16_t dest,uint16_t coefficient)
{
    uint16_t target,old,result;
    SYS_RUN(pcm_read16(pcm,source,&target));
    SYS_RUN(pcm_read16(pcm,dest,&old));
    SYS_RUN(sys_lag16(pcm,target,old,coefficient,&result));
    return pcm_write16(pcm,dest,result);
}

#endif
