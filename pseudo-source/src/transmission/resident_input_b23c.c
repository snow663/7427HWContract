#include "resident_input_private_3.h"

PcmStatus pcm_resident_input_b23c(Pcm *pcm)
{
    bool fault,set;
    uint8_t a,b,bias;
    uint16_t d,x,value;
    SYS_RUN(test(pcm,0x98,2,&fault));
    if(fault) {
        SYS_RUN(pcm_resident_gear_ratio(pcm,&x));
        SYS_RUN(pcm_read16(pcm,0xbd,&d));
        d=q(d>>2,x);
        SYS_RUN(test(pcm,0x9c,0x20,&set));
        if(set) {
            SYS_RUN(pcm_read16(pcm,0x5d1c,&x));
            d=double_sat(double_sat(pcm_resident_mul_f5a2(d,x)));
        }
    } else {
        SYS_RUN(pcm_read8(pcm,0x164,&a));
        SYS_RUN(pcm_read8(pcm,0x175,&b));
        if(a|b) SYS_RUN(pcm_read16(pcm,0xd5,&d));
        else {
            SYS_RUN(pcm_read16(pcm,0xcc,&d));
            SYS_RUN(pcm_read16(pcm,0xd3,&x));
            SYS_RUN(test(pcm,0x86,8,&set));
            SYS_RUN(pcm_write16(pcm,0xd5,set?x:0));
        }
    }
    SYS_RUN(pcm_write16(pcm,0xd1,d));
    SYS_RUN(pcm_read16(pcm,0xd3,&x));
    SYS_RUN(sys_lag16(pcm,d,x,0x5d1b,&value));
    SYS_RUN(pcm_write16(pcm,0xd3,value));
    SYS_RUN(pcm_read16(pcm,0xd3,&d));
    SYS_RUN(pcm_read16(pcm,0x5d1e,&x));
    d=q(d,x);
    a=(uint8_t)((d>>8)-128u);
    SYS_RUN(pcm_read8(pcm,0x102,&bias));
    int16_t signed_a=(a<128u)?a:(int16_t)a-256;
    int16_t signed_bias=(bias<128u)?bias:(int16_t)bias-256;
    int16_t sum=signed_a+signed_bias;
    if(sum>127) d=0x7fff;
    else if(sum< -128) d=0x8000;
    else d=(uint16_t)(((uint16_t)(uint8_t)sum<<8)|(d&255u));
    d=(uint16_t)(d+0x8000u);
    d=d>0xff7fu?UINT16_MAX:(uint16_t)(d+128u);
    SYS_RUN(pcm_write16(pcm,0x814,d));
    SYS_RUN(pcm_read16(pcm,0xd7,&x));
    SYS_RUN(sys_lag16(pcm,d,x,0x5d20,&value));
    return pcm_write16(pcm,0xd7,value);
}
