#include "egr_internal.h"
#include "reference_math.h"
/* D03E..D14D. The fraction word feeds fuel and spark. A zero FDIV divisor
 * retains the stock overflow quotient, including when the flow byte is zero. */
PcmStatus pcm_egr_flow(Pcm *pcm)
{
    uint8_t flags,option,position,value,coordinate,target=0;uint16_t old,denominator;
    SYS_RUN(pcm_read8(pcm,0x400d,&option));bool backpressure=(option&0x20u)!=0;
    if (!backpressure) { SYS_RUN(pcm_read8(pcm,0x400d,&option));backpressure=(option&4u)!=0; }
    SYS_RUN(sys_update(pcm,0x006e,0x80,0));
    SYS_RUN(pcm_read8(pcm,0x0070,&flags));
    if (backpressure) {
        if (flags&1u) goto filter;
        SYS_RUN(pcm_read8(pcm,0x0070,&flags));
        if (!(flags&4u)) {
            SYS_RUN(pcm_read8(pcm,0x01af,&value));if (value==0) goto filter;
            SYS_RUN(sys_update(pcm,0x006e,0,0x80));
        }
        SYS_RUN(pcm_read8(pcm,0x01c9,&value));value=(uint8_t)(0u-value);
        coordinate=value<=64u?(uint8_t)(value*2u):(uint8_t)(128u+((value-64u)>>1));
        if (coordinate>192u) coordinate=192;
        SYS_RUN(pcm_read8(pcm,0x0062,&value));if (value>160u) value=160;
        SYS_RUN(egr_surface(pcm,(uint8_t)(value>>1),coordinate,0x478a,&target));
        goto filter;
    }
    if (flags&1u) goto no_flow;
    SYS_RUN(pcm_read8(pcm,0x0072,&flags));if (flags&0x20u) goto no_flow;
    SYS_RUN(pcm_read8(pcm,0x0070,&flags));
    if (!(flags&4u)) {
        SYS_RUN(pcm_read8(pcm,0x400d,&option));
        if (option&2u) {
            SYS_RUN(pcm_read8(pcm,0x400d,&option));
            if (option&0x10u) { SYS_RUN(pcm_read8(pcm,0x0050,&flags));if (flags&0x80u) goto no_flow; }
            SYS_RUN(pcm_read8(pcm,0x01b9,&position));SYS_RUN(pcm_read8(pcm,0x485a,&value));
            if (position<value) goto no_flow;
            SYS_RUN(pcm_read16(pcm,0x00fd,&old));SYS_RUN(pcm_read16(pcm,0x485b,&denominator));
            if (old<denominator) goto no_flow;
        } else {
            SYS_RUN(pcm_read8(pcm,0x01af,&position));SYS_RUN(pcm_read8(pcm,0x485d,&value));
            if (position<value) goto no_flow;
        }
        SYS_RUN(sys_update(pcm,0x006e,0,0x80));SYS_RUN(pcm_read8(pcm,0x01b9,&position));
        SYS_RUN(pcm_read8(pcm,0x400d,&option));
        if (!(option&2u)) SYS_RUN(pcm_read8(pcm,0x01ae,&position));
    } else { SYS_RUN(pcm_read8(pcm,0x01ae,&position)); }
    coordinate=(uint8_t)(((uint16_t)position*160u+128u)>>8);
    SYS_RUN(pcm_read8(pcm,0x0232,&value));SYS_RUN(sys_curve16(pcm,value,0x47d3,&value));
    SYS_RUN(pcm_read8(pcm,0x01c9,&position));
    unsigned sum=(unsigned)value+(uint8_t)(0u-position);value=sum>255u?255:(uint8_t)sum;
    SYS_RUN(pcm_write8(pcm,0x01b0,value));
    if (value>=64u) { value=(uint8_t)(64u+((value-64u)>>1));if (value>=144u) value=144; }
    SYS_RUN(egr_surface(pcm,coordinate,value,0x47e5,&value));
    goto divide;
no_flow:
    value=0;
divide:
    SYS_RUN(pcm_write8(pcm,0x01b1,value));SYS_RUN(pcm_read8(pcm,0x47e4,&position));
    uint16_t numerator=(uint16_t)(((uint16_t)value*position+1u)>>1);
    SYS_RUN(pcm_read16(pcm,0x0232,&denominator));
    uint16_t quotient=denominator==0 || numerator>=denominator?65535u:
        (uint16_t)(((uint32_t)numerator<<16)/denominator);
    target=(uint8_t)(quotient>>8);
    if (target!=255u && (quotient&0x80u)) ++target;
filter:
    SYS_RUN(pcm_read8(pcm,0x01cc,&value));value=value<96u?0:(uint8_t)(value-96u);
    SYS_RUN(sys_curve16(pcm,value,0x4856,&value));
    target=(uint8_t)(((uint16_t)target*value+128u)>>8);
    SYS_RUN(pcm_read8(pcm,0x0232,&value));if (value>64u) value=64;
    SYS_RUN(sys_curve16(pcm,value,0x47ce,&value));SYS_RUN(pcm_read16(pcm,0x01b2,&old));
    return pcm_write16(pcm,0x01b2,pcm_lag8(target,old,value));
}
