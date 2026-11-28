#include "batch3.h"
#include "batch1.h"
#include "batch2.h"
#include "reference_math.h"
#include "../src/system/system_internal.h"

static uint16_t q(uint16_t d,uint16_t x)
{
    return x && d<x ? (uint16_t)(((uint32_t)d<<16)/x) : UINT16_MAX;
}
static uint16_t double_sat(uint16_t d)
{
    return d>0x7fffu ? UINT16_MAX : (uint16_t)(d<<1);
}
static uint16_t clamp_difference(uint16_t a,uint16_t b)
{
    int32_t d=(int32_t)a-b;
    if(d>32767) return 0x7fff;
    if(d< -32768) return 0x8000;
    return (uint16_t)d;
}
static PcmStatus test(Pcm *pcm,uint16_t a,uint8_t mask,bool *set)
{
    uint8_t v;
    SYS_RUN(pcm_read8(pcm,a,&v));
    *set=(v&mask)!=0;
    return PCM_OK;
}
/* F5A2: four byte products assemble the high word, no rounding. */
uint16_t closure_mul_f5a2(uint16_t d,uint16_t x)
{
    return (uint16_t)(((uint32_t)d*x)>>16);
}
/* F420 chooses correction using the N flag of the wrapped subtraction,
 * unlike F436 which uses its borrow. Reread the coefficient as in ROM. */
PcmStatus closure_lag_f420(Pcm *pcm,uint16_t target,uint16_t old,
                            uint16_t coefficient,uint16_t *result)
{
    uint16_t delta=(uint16_t)(target-old);
    uint8_t gain;
    SYS_RUN(pcm_read8(pcm,coefficient,&gain));
    uint16_t part=(uint16_t)(old+(delta>>8)*gain);
    if(delta&0x8000u) {
        SYS_RUN(pcm_read8(pcm,coefficient,&gain));
        part=(uint16_t)(part-(uint16_t)gain*256u);
    }
    SYS_RUN(pcm_read8(pcm,coefficient,&gain));
    *result=(uint16_t)(part+(((delta&255u)*gain+128u)>>8));
    return PCM_OK;
}
/* E58C: unchanged-count exit returns the remaining timeout, NOT the
 * retained speed. The changed-count/zero-timeout path retains old speed. */
PcmStatus closure_capture_e58c(Pcm *pcm,uint16_t record,uint16_t gain,
                               uint8_t reload,uint16_t *result)
{
    uint8_t now,old,timeout;
    uint16_t capture,previous;
    SYS_RUN(pcm_read8(pcm,record+8u,&now));
    SYS_RUN(pcm_read8(pcm,record,&old));
    uint8_t delta=(uint8_t)(now-old);
    SYS_RUN(pcm_read8(pcm,record+3u,&timeout));
    if(!delta) {
        if(timeout) {
            --timeout;
            SYS_RUN(pcm_write8(pcm,record+3u,timeout));
            if(timeout) { *result=timeout; return PCM_OK; }
        }
        *result=0;
        return pcm_write16(pcm,record+4u,0);
    }
    if(timeout) {
        SYS_RUN(pcm_read16(pcm,record+6u,&capture));
        SYS_RUN(pcm_read16(pcm,record+1u,&previous));
        uint16_t speed=q(q((uint16_t)delta*8u,gain),(uint16_t)(capture-previous));
        SYS_RUN(pcm_write16(pcm,record+4u,speed));
    }
    SYS_RUN(pcm_read16(pcm,record+6u,&capture));
    SYS_RUN(pcm_write16(pcm,record+1u,capture));
    SYS_RUN(pcm_read8(pcm,record+8u,&now));
    SYS_RUN(pcm_write8(pcm,record,now));
    SYS_RUN(pcm_write8(pcm,record+3u,reload));
    return pcm_read16(pcm,record+4u,result);
}
/* AEA4..B00F: raw input state, qualified hold masks, two protected
 * capture records and their independently retained estimator history. */
PcmStatus closure_input_aea4(Pcm *pcm)
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
    SYS_RUN(closure_capture_e58c(pcm,0xb9,gain,b,&d));
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
    SYS_RUN(closure_capture_e58c(pcm,0xc8,gain,b,&d));
    SYS_RUN(test(pcm,0x9c,0x20,&set));
    if(set) {
        SYS_RUN(pcm_read16(pcm,0x5d1c,&gain));
        d=double_sat(double_sat(closure_mul_f5a2(d,gain)));
    }
    return pcm_write16(pcm,0xcc,d);
}
PcmStatus closure_input_b018(Pcm *pcm)
{
    uint8_t a,b,limit,temp,index;
    uint16_t old;
    bool manual,range_fault,range;
    SYS_RUN(pcm_read8(pcm,0x9f,&a));
    SYS_RUN(pcm_write8(pcm,0xa0,a));
    SYS_RUN(test(pcm,0x5d02,0x20,&manual));
    if(manual) {
        SYS_RUN(test(pcm,0x98,4,&range_fault));
        if(!range_fault) {
            SYS_RUN(test(pcm,0xa2,2,&range));
            if(range) {
                SYS_RUN(pcm_write8(pcm,0x9f,0));
                return pcm_update8(pcm,0x9f,0,4);
            }
        }
    }
    SYS_RUN(pcm_read16(pcm,0x1a2,&old));
    SYS_RUN(pcm_read8(pcm,0x1a1,&temp));
    SYS_RUN(pcm_read8(pcm,0x5d2a,&a));
    old=pcm_lag8(temp,old,a);
    SYS_RUN(pcm_write16(pcm,0x1a2,old));
    a=(uint8_t)(old>>8);
    SYS_RUN(pcm_read8(pcm,0x5d2c,&limit));
    if(a<limit) {
        SYS_RUN(pcm_read8(pcm,0x5d2b,&limit));
        index=a<limit?0:1;
    } else {
        SYS_RUN(pcm_read8(pcm,0x5d2d,&limit));
        if(a<limit) index=2;
        else {
            SYS_RUN(pcm_read8(pcm,0x5d2e,&limit));
            index=a<limit?3:4;
        }
    }
    SYS_RUN(pcm_read8(pcm,0xb084u+index,&a));
    SYS_RUN(pcm_read8(pcm,0x1a4,&b));
    if(a!=b) SYS_RUN(pcm_write8(pcm,0x1a5,0));
    else {
        SYS_RUN(pcm_read8(pcm,0x1a5,&b));
        SYS_RUN(pcm_read8(pcm,0x5d29,&limit));
        if(b>=limit) SYS_RUN(pcm_write8(pcm,0x9f,a));
        else if((uint8_t)(b+1u)) SYS_RUN(pcm_write8(pcm,0x1a5,(uint8_t)(b+1u)));
    }
    return pcm_write8(pcm,0x1a4,a);
}
PcmStatus closure_input_b089(Pcm *pcm)
{
    uint8_t a,b;
    bool fault,enabled;
    SYS_RUN(closure_diag_e8c8(pcm));
    SYS_RUN(closure_diag_eccc(pcm));
    SYS_RUN(closure_fault_e6f5(pcm));
    SYS_RUN(test(pcm,0x98,4,&fault));
    if(fault) SYS_RUN(pcm_write8(pcm,0xa2,0x88));
    SYS_RUN(pcm_read8(pcm,0x9f,&a));
    SYS_RUN(test(pcm,0x5b32,0x20,&enabled));
    if(enabled) {
        SYS_RUN(test(pcm,0x1d,0x20,&fault));
        if(fault) {
            SYS_RUN(pcm_write8(pcm,0x9f,(a&0xf0u)|9u));
            goto diagnostics;
        }
    }
    if(a&4u) {
        SYS_RUN(test(pcm,0x98,4,&fault));
        if(!fault) {
            SYS_RUN(pcm_read8(pcm,0x5d0f,&b));
            if(b) {
                SYS_RUN(pcm_write8(pcm,0x9f,a^5u));
            }
        }
    }
diagnostics:
    SYS_RUN(closure_diag_e7c7(pcm));
    SYS_RUN(closure_diag_e808(pcm));
    SYS_RUN(closure_fault_e5cf(pcm));
    SYS_RUN(closure_diag_ebc0(pcm));
    SYS_RUN(test(pcm,0x400f,0x80,&enabled));
    if(!enabled) SYS_RUN(closure_diag_e847(pcm));
    SYS_RUN(closure_diag_ef2b(pcm));
    SYS_RUN(closure_diag_eb81(pcm));
    SYS_RUN(closure_fault_e60b(pcm));
    /* E6E4 is literal RTS. */
    return closure_fault_e5f1(pcm);
}
static PcmStatus lag_store(Pcm *pcm,uint16_t source,uint16_t dest,uint16_t coefficient)
{
    uint16_t target,old,result;
    SYS_RUN(pcm_read16(pcm,source,&target));
    SYS_RUN(pcm_read16(pcm,dest,&old));
    SYS_RUN(sys_lag16(pcm,target,old,coefficient,&result));
    return pcm_write16(pcm,dest,result);
}
PcmStatus closure_input_b1f0(Pcm *pcm)
{
    uint16_t a,b,old,value;
    SYS_RUN(lag_store(pcm,0xb7,0x1ac,0x5d10));
    SYS_RUN(lag_store(pcm,0xbd,0xc2,0x5d14));
    SYS_RUN(lag_store(pcm,0xc4,0xc6,0x5d17));
    SYS_RUN(pcm_read16(pcm,0xb7,&a));
    SYS_RUN(pcm_read16(pcm,0xc4,&b));
    SYS_RUN(pcm_read16(pcm,0xeb,&old));
    SYS_RUN(closure_lag_f420(pcm,clamp_difference(a,b),old,0x5d0d,&value));
    SYS_RUN(pcm_write16(pcm,0xeb,value));
    return pcm_write16(pcm,0xed,(value&0x8000u)?(uint16_t)(0u-value):value);
}
PcmStatus closure_input_b23c(Pcm *pcm)
{
    bool fault,set;
    uint8_t a,b,bias;
    uint16_t d,x,value;
    SYS_RUN(test(pcm,0x98,2,&fault));
    if(fault) {
        SYS_RUN(closure_gear_ratio(pcm,&x));
        SYS_RUN(pcm_read16(pcm,0xbd,&d));
        d=q(d>>2,x);
        SYS_RUN(test(pcm,0x9c,0x20,&set));
        if(set) {
            SYS_RUN(pcm_read16(pcm,0x5d1c,&x));
            d=double_sat(double_sat(closure_mul_f5a2(d,x)));
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
/* C483: selectors reread flags at each decision, no cached global
 * snapshot. Each priority chain retains the literal first-match rule. */
PcmStatus closure_input_c483(Pcm *pcm)
{
    bool set;
    uint8_t v;
    SYS_RUN(test(pcm,0x9f,4,&set));
    if(set) v=1;
    else { SYS_RUN(test(pcm,0x9f,2,&set)); v=set?2:4; }
    SYS_RUN(pcm_write8(pcm,0x80,v));
    SYS_RUN(test(pcm,0x9f,4,&set));
    SYS_RUN(pcm_write8(pcm,0x82,set?1:2));
    SYS_RUN(test(pcm,0x87,2,&set));
    if(set) v=1;
    else {
        SYS_RUN(test(pcm,0x9f,4,&set));
        if(set) v=2;
        else { SYS_RUN(test(pcm,0x9f,2,&set)); v=set?4:8; }
    }
    SYS_RUN(pcm_write8(pcm,0x7f,v));
    SYS_RUN(test(pcm,0x87,4,&set));
    if(set) v=1;
    else {
        SYS_RUN(test(pcm,0x87,2,&set));
        if(set) v=2;
        else {
            SYS_RUN(test(pcm,0x9f,4,&set));
            if(set) v=4;
            else { SYS_RUN(test(pcm,0x9f,2,&set)); v=set?8:16; }
        }
    }
    return pcm_write8(pcm,0x81,v);
}
/* AE85 prefix only. The existing F781/F64E service tail remains
 * canonical and is a separate joined-entry verification obligation. */
PcmStatus closure_input_prefix(Pcm *pcm)
{
    SYS_RUN(closure_input_aea4(pcm));
    SYS_RUN(closure_input_b018(pcm));
    SYS_RUN(closure_input_b089(pcm));
    SYS_RUN(closure_input_c483(pcm));
    SYS_RUN(closure_input_b1f0(pcm));
    SYS_RUN(closure_input_b23c(pcm));
    SYS_RUN(closure_speed_ratio(pcm));
    return closure_temperature_class(pcm);
}
