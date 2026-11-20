#ifndef PCM_GOVERNOR_INTERNAL_H
#define PCM_GOVERNOR_INTERNAL_H
#include "fuel.h"
#include "hardware.h"
#define GOV_RUN(call) do { PcmStatus gov_status=(call); if(gov_status!=PCM_OK)return gov_status; } while(0)

/* In BMHM F4B6/F4C1, MUL sets C from product bit7, so the high-byte
 * interpolation rounds by 0x80. LDD 0,X captures adjacent bytes and
 * the original first byte is reread after multiplication. */
static inline PcmStatus governor_interpolate(Pcm *pcm,uint16_t start,uint8_t coordinate,
                                              uint8_t step,uint8_t *output)
{
    if (output==NULL)return PCM_BAD_CONFIGURATION;
    uint16_t point=(uint16_t)((uint16_t)coordinate*step);
    uint16_t address=(uint16_t)(start+(point>>8));
    uint16_t knots;
    GOV_RUN(pcm_read16(pcm,address,&knots));
    uint8_t first=(uint8_t)(knots>>8),second=(uint8_t)knots,base;
    uint8_t difference=first>=second?(uint8_t)(first-second):(uint8_t)(second-first);
    uint8_t interpolation=(uint8_t)(((uint16_t)difference*(uint8_t)point+128u)>>8);
    GOV_RUN(pcm_read8(pcm,address,&base));
    *output=first<second?(uint8_t)(base+interpolation):(uint8_t)(base-interpolation);
    return PCM_OK;
}
static inline PcmStatus governor_scaled_curve(Pcm *pcm,uint16_t header,uint8_t input,uint8_t *result)
{
    uint8_t step;
    GOV_RUN(pcm_read8(pcm,header,&step)); /* F4B8 LDAB 0,X */
    return governor_interpolate(pcm,(uint16_t)(header+1u),input,step,result);
}
static inline PcmStatus governor_capped_curve(Pcm *pcm,uint16_t header,uint8_t input,uint8_t *result)
{
    uint8_t cap;
    GOV_RUN(pcm_read8(pcm,header,&cap)); /* F49A CMPA 0,X */
    if(input>cap) GOV_RUN(pcm_read8(pcm,header,&input)); /* F49E LDAA 0,X */
    return governor_interpolate(pcm,(uint16_t)(header+1u),input,16u,result); /* F4BD */
}
static inline PcmStatus governor_fixed_curve(Pcm *pcm,uint16_t first,uint8_t input,uint8_t *result)
{
    return governor_interpolate(pcm,first,input,16u,result); /* F4C1 */
}
static inline uint16_t governor_sat_shift(uint16_t value,unsigned count)
{
    unsigned wide=(unsigned)value<<count;
    return wide>65535u?0xffffu:(uint16_t)wide;
}
/* F550 8x16 multiply. Low-byte partial is rounded first, then added to
 * the high-byte product. The original stock 16-bit operation wraps. */
static inline uint16_t governor_mul8x16(uint8_t scale,uint16_t word)
{
    uint8_t low=(uint8_t)word,high=(uint8_t)(word>>8);
    uint16_t partial=(uint16_t)(((uint16_t)scale*low+128u)>>8);
    return (uint16_t)((uint16_t)scale*high+partial);
}
#endif
