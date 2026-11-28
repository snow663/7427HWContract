#include "resident_input_private_3.h"

/* AEA4..B00F: raw input state, qualified hold masks, two protected
 * capture records and their independently retained estimator history. */
PcmStatus pcm_resident_input_aea4(Pcm *pcm)
{
    bool set,hold;
    uint8_t a,b,c,previous,change,options;
    uint16_t d,x,y,gain;
    SYS_RUN(pcm_update8(pcm,0x76,0x80,0));
    SYS_RUN(test(pcm,0x3000,0x40,&set));
    if(set) SYS_RUN(pcm_update8(pcm,0x76,0,0x80));
    SYS_RUN(pcm_read8(pcm,0x3002,&b));
    SYS_RUN(pcm_read8(pcm,0x3060,&a));
    SYS_RUN(pcm_read8(pcm,0x3062,&c));
    SYS_RUN(pcm_write8(pcm,0x9e,(uint8_t)(((a^c)&3u)<<4)|((uint8_t)~b&15u)));
    SYS_RUN(pcm_read8(pcm,0x9c,&a));
    SYS_RUN(pcm_write8(pcm,0x9d,a));
    SYS_RUN(pcm_update8(pcm,0x9c,4,0));
    SYS_RUN(test(pcm,0x3d,0x20,&set));
    if(set) SYS_RUN(pcm_update8(pcm,0x9c,0,4));
    SYS_RUN(pcm_update8(pcm,0x9c,0x80,0));
    SYS_RUN(test(pcm,0x50,0x10,&set));
    if(set) {
        SYS_RUN(test(pcm,0x86,0x80,&set));
        if(!set) SYS_RUN(pcm_update8(pcm,0x9c,0,0x80));
    }
    SYS_RUN(pcm_read8(pcm,0x4d,&b));
    SYS_RUN(pcm_read8(pcm,0x9b,&previous));
    change=b^previous;
    SYS_RUN(pcm_write8(pcm,0x9b,b));
    hold=false;
    if(change&1u) SYS_RUN(test(pcm,0x5d03,4,&hold));
    if(!hold) {
        SYS_RUN(pcm_update8(pcm,0x9c,2,0));
        if(b&1u) SYS_RUN(pcm_update8(pcm,0x9c,0,2));
    }
    hold=false;
    if(change&0x80u) {
        SYS_RUN(pcm_read8(pcm,0x5d2f,&a));
        SYS_RUN(pcm_write8(pcm,0x1ab,a));
        SYS_RUN(test(pcm,0x5d03,0x10,&hold));
    }
    if(!hold) {
        SYS_RUN(pcm_update8(pcm,0x9c,0,0x20));
        if(b&0x80u) SYS_RUN(pcm_update8(pcm,0x9c,0x20,0));
    }
    SYS_RUN(pcm_read8(pcm,0x1ab,&a));
    if(a) {
        SYS_RUN(pcm_read8(pcm,0x1ab,&a));
        SYS_RUN(pcm_write8(pcm,0x1ab,(uint8_t)(a-1u)));
    }
    hold=false;
    if(change&0x1cu) SYS_RUN(test(pcm,0x5d03,2,&hold));
    if(!hold) {
        SYS_RUN(pcm_read8(pcm,(uint16_t)(0xb010u+((b&0x1cu)>>2)),&c));
        SYS_RUN(pcm_read8(pcm,0xa1,&a));
        if((uint8_t)(a+1u)) SYS_RUN(pcm_write8(pcm,0xa1,(uint8_t)(a+1u)));
        SYS_RUN(pcm_read8(pcm,0xa2,&a));
        SYS_RUN(pcm_write8(pcm,0xa3,a));
        if(a!=c) {
            SYS_RUN(pcm_write8(pcm,0xa1,0));
            SYS_RUN(pcm_write8(pcm,0xa2,c));
        }
    }
    SYS_RUN(pcm_read8(pcm,0x76,&b));
    SYS_RUN(pcm_read8(pcm,0x77,&a));
    SYS_RUN(pcm_write8(pcm,0x77,b));
    hold=false;
    if((a^b)&0x80u) SYS_RUN(test(pcm,0x5d03,8,&hold));
    if(!hold) {
        SYS_RUN(pcm_update8(pcm,0x9c,0,0x40));
        if(b&0x80u) SYS_RUN(pcm_update8(pcm,0x9c,0x40,0));
    }
    SYS_RUN(pcm_read16(pcm,0x5f,&x));
    d=q(120,x);
    SYS_RUN(pcm_write16(pcm,0xb7,d>120u?d:0));
    SYS_RUN(pcm_mask_irq(pcm,true));
    SYS_RUN(pcm_read8(pcm,0x3027,&b));
    SYS_RUN(pcm_read16(pcm,0x3010,&y));
    SYS_RUN(pcm_read8(pcm,0x3027,&a));
    if(a!=b) {
        SYS_RUN(pcm_read16(pcm,0x3010,&y));
        ++b;
    }
    SYS_RUN(pcm_write8(pcm,0xc1,b));
    SYS_RUN(pcm_write16(pcm,0xbf,y));
    SYS_RUN(pcm_mask_irq(pcm,false));
    SYS_RUN(pcm_read8(pcm,0x5d11,&b));
    SYS_RUN(pcm_read16(pcm,0x5d12,&gain));
    SYS_RUN(pcm_resident_capture_e58c(pcm,0xb9,gain,b,&d));
    SYS_RUN(pcm_write16(pcm,0xbd,d));
    SYS_RUN(pcm_read16(pcm,0xbd,&x));
    SYS_RUN(pcm_read8(pcm,0xd9,&a));
    if(a>=3) {
        SYS_RUN(pcm_read16(pcm,0x5d15,&gain));
        x=q(x>>1,gain);
    }
    SYS_RUN(pcm_write16(pcm,0xc4,x));
    SYS_RUN(pcm_read8(pcm,0x5d02,&options));
    uint16_t count=(options&0x10u)?0x3fc6:0x3fe0;
    uint16_t stamp=(options&0x10u)?0x3ff8:0x3fc2;
    SYS_RUN(pcm_mask_irq(pcm,true));
    SYS_RUN(pcm_read16(pcm,count,&d));
    SYS_RUN(pcm_delay_cycles(pcm,11));
    SYS_RUN(pcm_read16(pcm,stamp,&y));
    SYS_RUN(pcm_delay_cycles(pcm,11));
    SYS_RUN(pcm_read16(pcm,count,&x));
    b=(uint8_t)d;
    if(x!=d) {
        SYS_RUN(pcm_delay_cycles(pcm,11));
        SYS_RUN(pcm_read16(pcm,stamp,&y));
        ++b;
    }
    SYS_RUN(pcm_write8(pcm,0xd0,b));
    SYS_RUN(pcm_write16(pcm,0xce,y));
    SYS_RUN(pcm_mask_irq(pcm,false));
    SYS_RUN(pcm_read16(pcm,0x5d19,&gain));
    SYS_RUN(pcm_read8(pcm,0x5d18,&b));
    SYS_RUN(pcm_resident_capture_e58c(pcm,0xc8,gain,b,&d));
    SYS_RUN(test(pcm,0x9c,0x20,&set));
    if(set) {
        SYS_RUN(pcm_read16(pcm,0x5d1c,&gain));
        d=double_sat(double_sat(pcm_resident_mul_f5a2(d,gain)));
    }
    return pcm_write16(pcm,0xcc,d);
}
