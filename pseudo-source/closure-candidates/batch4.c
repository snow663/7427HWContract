#include "batch4.h"
#include "control.h"
#include <stdio.h>
#include <stdlib.h>
/* Diagnostic output only during a replay of a preserved counterexample. */
static void pressure_trace(const char *stage,uint8_t value)
{ if(getenv("PCM_CLOSURE_TRACE")) fprintf(stderr,"%s=%02x ",stage,(unsigned)value); }

#include "../src/emissions/egr_internal.h"

static int32_t s16(uint16_t x) { return x<0x8000u?(int32_t)x:(int32_t)x-65536; }
static int s8(uint8_t x) { return x<128u?(int)x:(int)x-256; }
static uint8_t sat8(int x) { return (uint8_t)(x>127?127:x< -128?-128:x); }
static uint16_t sat16(int32_t x) { return (uint16_t)(x>32767?32767:x< -32768?-32768:x); }
static uint8_t add8(uint8_t a,uint8_t b) { return sat8(s8(a)+s8(b)); }
static uint8_t sub8(uint8_t a,uint8_t b) { return sat8(s8(a)-s8(b)); }
static PcmStatus test(Pcm *pcm,uint16_t a,uint8_t m,bool *set)
{
    uint8_t v;
    SYS_RUN(pcm_read8(pcm,a,&v));
    *set=(v&m)!=0;
    return PCM_OK;
}
static PcmStatus curve(Pcm *pcm,uint16_t table,uint16_t input,uint8_t *v)
{
    uint8_t a;
    SYS_RUN(pcm_read8(pcm,input,&a));
    return sys_curve16(pcm,a,table,v);
}
static PcmStatus indexed_curve(Pcm *pcm,uint16_t table,uint8_t offset,uint8_t *v)
{
    uint16_t ptr;
    SYS_RUN(pcm_read16(pcm,(uint16_t)(table+offset),&ptr));
    return curve(pcm,ptr,0xb2,v);
}
static PcmStatus copy8(Pcm *pcm,uint16_t from,uint16_t to)
{
    uint8_t a;
    SYS_RUN(pcm_read8(pcm,from,&a));
    return pcm_write8(pcm,to,a);
}
static PcmStatus copy16(Pcm *pcm,uint16_t from,uint16_t to)
{
    uint16_t a;
    SYS_RUN(pcm_read16(pcm,from,&a));
    return pcm_write16(pcm,to,a);
}
static PcmStatus shape_rate(Pcm *pcm,uint16_t table,uint8_t index,uint16_t *out)
{
    uint8_t v;
    uint16_t old;
    SYS_RUN(indexed_curve(pcm,table,index,&v));
    SYS_RUN(pcm_read16(pcm,0x13e,&old));
    *out=sat16(s16(old)+8*((int)v-128));
    return PCM_OK;
}
static PcmStatus shape_seed(Pcm *pcm,uint8_t index)
{
    uint8_t v;
    bool seeded;
    SYS_RUN(test(pcm,0x8f,1,&seeded));
    if(seeded) return PCM_OK;
    SYS_RUN(indexed_curve(pcm,0xbe55,index,&v));
    SYS_RUN(pcm_write16(pcm,0x13e,(uint16_t)((uint16_t)(uint8_t)(v-128u)<<8)));
    return pcm_update8(pcm,0x8f,0,1);
}
/* BCC6..BE36. Return D as well as its retained 013E publication. */
PcmStatus closure_pressure_shape(Pcm *pcm,uint16_t *out)
{
    bool fault,range,event,latch;
    uint8_t gear,index,age,v,limit;
    uint16_t ratio,bound,result=0;
    SYS_RUN(test(pcm,0x98,4,&fault));
    if(!fault) SYS_RUN(test(pcm,0xa2,0x70,&fault));
    if(fault) {
        SYS_RUN(pcm_update8(pcm,0x8e,1,0));
        goto publish;
    }
    SYS_RUN(test(pcm,0x83,1,&event));
    if(event) {
        SYS_RUN(pcm_update8(pcm,0x8e,0,1));
        SYS_RUN(pcm_update8(pcm,0x8f,1,0));
        SYS_RUN(pcm_write8(pcm,0x13d,0));
        SYS_RUN(pcm_write8(pcm,0x13c,0));
        goto publish;
    }
    SYS_RUN(test(pcm,0x83,8,&event));
    if(event) goto steady;
    SYS_RUN(test(pcm,0x8e,1,&latch));
    if(!latch) goto steady;
    SYS_RUN(pcm_read8(pcm,0xd9,&gear));
    index=(uint8_t)(gear-1u);
    if(index&128u) goto steady;
    SYS_RUN(pcm_read8(pcm,0xdb,&age));
    SYS_RUN(pcm_read8(pcm,0x5f2du+index,&limit));
    if(age>=limit) goto steady;
    if(index<2) {
        index=(uint8_t)(2u*index);
        SYS_RUN(pcm_read16(pcm,0x5f19u+index,&bound));
        SYS_RUN(pcm_read16(pcm,0xf9,&ratio));
        if(bound<=ratio) goto publish;
        SYS_RUN(test(pcm,0x91,0x10,&range));
        if(range) goto steady;
        SYS_RUN(shape_seed(pcm,index));
        SYS_RUN(pcm_read8(pcm,0xd9,&gear));
        index=(uint8_t)(2u*(uint8_t)(gear-1u));
        SYS_RUN(indexed_curve(pcm,0xbe37,index,&v));
        SYS_RUN(pcm_read8(pcm,0xf9,&age));
        if(v<age) {
            SYS_RUN(shape_rate(pcm,0xbe3d,index,&result));
            goto publish;
        }
        SYS_RUN(pcm_read16(pcm,0x5f1du+index,&bound));
        SYS_RUN(pcm_read16(pcm,0xf9,&ratio));
        if(bound>=ratio) {
            SYS_RUN(pcm_read8(pcm,0x13d,&age));
            SYS_RUN(pcm_write8(pcm,0x13d,(uint8_t)(age+1u)));
            SYS_RUN(indexed_curve(pcm,0xbe49,index,&v));
            SYS_RUN(pcm_read8(pcm,0x13d,&age));
            if(v<age) goto steady;
        }
        SYS_RUN(shape_rate(pcm,0xbe43,index,&result));
        goto publish;
    }
    SYS_RUN(curve(pcm,0x6864,0xb2,&v));
    SYS_RUN(pcm_read8(pcm,0x13c,&age));
    if(v>=age) {
        SYS_RUN(copy8(pcm,0xdb,0x13c));
        goto publish;
    }
    SYS_RUN(curve(pcm,0x6787,0xb2,&v));
    SYS_RUN(pcm_read8(pcm,0x13c,&age));
    unsigned sum=(unsigned)v+age;
    SYS_RUN(pcm_read8(pcm,0xdb,&limit));
    if((sum>255u?255u:sum)>=limit) {
        SYS_RUN(shape_seed(pcm,4));
        SYS_RUN(shape_rate(pcm,0xbe3d,4,&result));
        goto publish;
    }
    SYS_RUN(indexed_curve(pcm,0xbe49,4,&v));
    SYS_RUN(pcm_read8(pcm,0x13d,&age));
    if(v<age) goto steady;
    SYS_RUN(pcm_write8(pcm,0x13d,(uint8_t)(age+1u)));
    SYS_RUN(shape_rate(pcm,0xbe43,4,&result));
    goto publish;
steady:
    SYS_RUN(pcm_update8(pcm,0x8e,1,0));
    SYS_RUN(pcm_read8(pcm,0xd9,&gear));
    if(gear) {
        SYS_RUN(curve(pcm,(uint16_t)(0x6754u+(uint8_t)(17u*(gear-1u))),0xb2,&v));
        result=(uint16_t)((uint16_t)(uint8_t)(v-128u)<<8);
    }
publish:
    *out=result;
    return pcm_write16(pcm,0x13e,result);
}
static PcmStatus pattern_index(Pcm *pcm,uint8_t *index)
{
    bool set;
    SYS_RUN(test(pcm,0x9f,6,&set));
    if(set) {
        *index=(uint8_t)(*index+3u);
        SYS_RUN(test(pcm,0x9f,2,&set));
        if(!set) *index=(uint8_t)(*index+3u);
    }
    *index=(uint8_t)(*index<<1);
    return PCM_OK;
}
static PcmStatus down_snapshot(Pcm *pcm,uint8_t *gear)
{
    bool set;
    SYS_RUN(pcm_read8(pcm,0xd9,gear));
    SYS_RUN(test(pcm,0x83,0x10,&set));
    if(set) ++*gear;
    return PCM_OK;
}
/* B60B..B66B: literal stack numerator and unsigned quotient. */
static PcmStatus temperature_column(Pcm *pcm,uint8_t *col)
{
    uint8_t t,first,last,upper,lower;
    SYS_RUN(pcm_read8(pcm,0xb2,&t));
    SYS_RUN(pcm_read8(pcm,0x5f28,&first));
    if(t<=first) { *col=0; return PCM_OK; }
    SYS_RUN(pcm_read8(pcm,0x5f2b,&last));
    if(t>=last) { *col=48; return PCM_OK; }
    uint16_t ptr=0x5f29;
    uint8_t base=16;
    for(unsigned i=0;i<256;++i) {
        SYS_RUN(pcm_read8(pcm,ptr,&upper));
        if(t<upper) {
            SYS_RUN(pcm_read8(pcm,ptr,&upper));
            SYS_RUN(pcm_read8(pcm,ptr-1u,&lower));
            uint8_t span=(uint8_t)(upper-lower);
            SYS_RUN(pcm_read8(pcm,ptr,&upper));
            uint16_t numerator=(uint16_t)((int32_t)span*base+16*(int32_t)t-16*(int32_t)upper);
            *col=span?(uint8_t)(numerator/span):255;
            return PCM_OK;
        }
        ++ptr; base=(uint8_t)(base+16u);
    }
    return PCM_BAD_CONFIGURATION;
}
static PcmStatus pressure_baro(Pcm *pcm,uint8_t gain,uint8_t *value)
{
    uint8_t baro;
    SYS_RUN(pcm_read8(pcm,0xac,&baro));
    uint16_t product=(uint16_t)((uint8_t)(baro-128u)*(uint16_t)gain);
    SYS_RUN(pcm_read8(pcm,0xac,&baro));
    if(!(baro&128u)) product=(uint16_t)(product-(uint16_t)gain*256u);
    uint16_t d=s8((uint8_t)(product>>8))+64>0?(uint16_t)((product+0x4000u)<<1):0;
    d=(uint16_t)(d+128u);
    uint16_t p=(uint16_t)((d>>8)*(uint16_t)*value);
    *value=p>=16384u?127:(uint8_t)(p>>7);
    return PCM_OK;
}
static PcmStatus speed_floor(Pcm *pcm,uint8_t *pressure)
{
    bool set;
    uint8_t age,gear,v;
    uint16_t prev,bound,table=0;
    SYS_RUN(pcm_update8(pcm,0x8e,4,0));
    SYS_RUN(test(pcm,0x83,9,&set));
    if(set) {
        SYS_RUN(pcm_write8(pcm,0xe8,0));
        SYS_RUN(pcm_read16(pcm,0xef,&prev));
        SYS_RUN(pcm_read16(pcm,0x5f26,&bound));
        if(s16(prev)<s16(bound)) goto choose;
        SYS_RUN(copy8(pcm,0x5f25,0xe8));
    }
    SYS_RUN(pcm_read8(pcm,0xe8,&age));
    if(age) {
        SYS_RUN(pcm_write8(pcm,0xe8,(uint8_t)(age-1u)));
        goto finish;
    }
choose:
    SYS_RUN(test(pcm,0x98,4,&set));
    if(set) table=0x5f96;
    else {
        SYS_RUN(pcm_read8(pcm,0xd9,&gear));
        if(gear==3) goto finish;
        SYS_RUN(test(pcm,0xa2,7,&set));
        if(!set) goto finish;
        if(gear==2) table=0x5fa7;
        else {
            SYS_RUN(test(pcm,0xa2,3,&set));
            if(!set) goto finish;
            if(gear) table=0x5f96;
            else {
                SYS_RUN(test(pcm,0xa2,1,&set));
                if(!set) goto finish;
                table=0x5f85;
            }
        }
    }
    SYS_RUN(curve(pcm,table,0xd7,&v));
    SYS_RUN(pcm_write8(pcm,0x143,v));
    if(v>=*pressure) {
        *pressure=v;
        SYS_RUN(pcm_update8(pcm,0x8e,0,4));
    }
finish:
    SYS_RUN(copy16(pcm,0xeb,0xef));
    return pcm_write8(pcm,0x145,*pressure);
}
static PcmStatus engagement(Pcm *pcm,uint8_t *pressure)
{
    bool set,entry,reverse;
    uint8_t speed,limit,age,v,b,temp,deadband;
    uint16_t table=0,d;
    SYS_RUN(pcm_read8(pcm,0xd7,&speed));
    SYS_RUN(test(pcm,0xa2,0x50,&set));
    if(set) {
        SYS_RUN(pcm_update8(pcm,0x8e,0x30,0));
        SYS_RUN(pcm_read8(pcm,0x5f11,&limit));
        if(speed>=limit) goto clear;
        SYS_RUN(pcm_update8(pcm,0x8e,2,0));
        table=0x5fb8;
        SYS_RUN(pcm_read8(pcm,0x5f13,&deadband));
        goto seed;
    }
    SYS_RUN(pcm_read8(pcm,0x5f12,&limit));
    if(speed>=limit) {
        SYS_RUN(pcm_update8(pcm,0x8e,0x30,0));
        goto clear;
    }
    SYS_RUN(test(pcm,0xa2,0xf,&set));
    SYS_RUN(test(pcm,0xa3,set?0xf:0x20,&entry));
    if(entry) {
        SYS_RUN(test(pcm,0x8e,2,&set));
        if(!set) return PCM_OK;
        goto shape;
    }
    SYS_RUN(pcm_update8(pcm,0x8e,0,2));
    SYS_RUN(test(pcm,0xa2,0x20,&reverse));
    if(reverse) {
        SYS_RUN(pcm_update8(pcm,0x8e,0,0x10));
        SYS_RUN(pcm_update8(pcm,0x8e,0x20,0));
        SYS_RUN(copy8(pcm,0x5f0f,0x141));
        table=0x6043;
        SYS_RUN(pcm_read8(pcm,0x5f15,&deadband));
    } else {
        SYS_RUN(pcm_update8(pcm,0x8e,0x10,0));
        SYS_RUN(pcm_update8(pcm,0x8e,0,0x20));
        SYS_RUN(copy8(pcm,0x5f0d,0x141));
        table=0x5fb8;
        SYS_RUN(pcm_read8(pcm,0x5f14,&deadband));
    }
seed:
    SYS_RUN(pcm_write8(pcm,0x140,deadband));
    SYS_RUN(pcm_read16(pcm,0xc2,&d));
    /* B7BC..B7C9: preserve low byte on first/second ASLD carry;
     * LDAA FF does not replace B. ADDD 0080 then SBCA 00. */
    bool carry=(d&0x8000u)!=0;
    d=(uint16_t)(d<<1);
    if(!carry) { carry=(d&0x8000u)!=0; d=(uint16_t)(d<<1); }
    if(carry) d=(uint16_t)(0xff00u|(uint8_t)d);
    uint32_t rounded=(uint32_t)d+128u;
    b=(uint8_t)((rounded>>8)-(rounded>65535u));
    SYS_RUN(pcm_read8(pcm,0xb5,&temp));
    unsigned coord=((uint16_t)temp*154u+128u)>>8;
    SYS_RUN(egr_surface(pcm,coord>112u?112:(uint8_t)coord,b,table,&v));
    SYS_RUN(pcm_write8(pcm,0x146,(uint8_t)(v-128u)));
shape:
    SYS_RUN(pcm_read8(pcm,0xb2,&temp));
    SYS_RUN(pcm_read8(pcm,0xd7,&speed));
    SYS_RUN(egr_surface(pcm,temp,(uint8_t)(2u*(speed>32u?32u:speed)),0x60ce,&v));
    SYS_RUN(pcm_read8(pcm,0x146,&b));
    v=(uint8_t)(add8((uint8_t)(v-128u),b)+128u);
    SYS_RUN(pcm_read8(pcm,0x141,&age));
    if(age) {
        SYS_RUN(test(pcm,0x8e,0x20,&set));
        if(set) {
            SYS_RUN(pcm_read8(pcm,0x5f0e,&b)); v=(uint8_t)(v+b);
        } else {
            SYS_RUN(test(pcm,0x8e,0x10,&set));
            if(set) { SYS_RUN(pcm_read8(pcm,0x5f10,&b)); v=(uint8_t)(v+b); }
        }
        SYS_RUN(pcm_write8(pcm,0x141,(uint8_t)(age-1u)));
        SYS_RUN(pcm_write8(pcm,0x144,v));
    } else {
        SYS_RUN(pcm_write8(pcm,0x144,v));
        SYS_RUN(pcm_update8(pcm,0x8e,0x30,0));
    }
    SYS_RUN(pcm_read8(pcm,0x144,&b));
    SYS_RUN(pcm_read8(pcm,0x145,pressure));
    SYS_RUN(pcm_read8(pcm,0x140,&deadband));
    unsigned sum=(unsigned)b+deadband;
    if(sum>255u||s8(*pressure)<s8((uint8_t)sum))
        return pcm_read8(pcm,0x144,pressure);
clear:
    SYS_RUN(pcm_update8(pcm,0x8e,2,0));
    return pcm_write8(pcm,0x141,0);
}
/* B587..B88C, stage order and headroom state preserved. */
PcmStatus closure_pressure_main(Pcm *pcm)
{
    uint8_t a,b,v,gear,index,throttle,temp,col,cap;
    uint16_t table,shape;
    bool set;
    SYS_RUN(pcm_read8(pcm,0x111,&a));
    if(a) return pcm_write8(pcm,0xe2,a);
    SYS_RUN(pcm_read8(pcm,0x9f,&b));
    SYS_RUN(test(pcm,0xa2,0x20,&set));
    v=0;
    if(!set) SYS_RUN(pcm_read8(pcm,0xd7,&v));
    SYS_RUN(pcm_read16(pcm,(uint16_t)((v&128u?0xb967u:0xb961u)+(b&6u)),&table));
    SYS_RUN(pcm_read8(pcm,0xb2,&throttle));
    SYS_RUN(egr_surface(pcm,throttle,(uint8_t)(2u*v),table,&a));
    pressure_trace("B5AC",a);
    SYS_RUN(down_snapshot(pcm,&gear));
    index=(uint8_t)(gear-1u);
    if(!(index&128u)) {
        SYS_RUN(pcm_read8(pcm,0x115u+index,&v));
        if(!v) {
            SYS_RUN(pattern_index(pcm,&index));
            SYS_RUN(pcm_read16(pcm,0xb96du+index,&table));
            if(table) {
                SYS_RUN(curve(pcm,table,0xb2,&v));
                v=(uint8_t)(v-128u);
            }
        }
        a=add8(a,v);
    }
    pressure_trace("B5E3",a);
    SYS_RUN(pcm_pressure_adaptive_cell(pcm,&v));
    int reduced=s8(v);
    reduced=reduced>=0?reduced/8:-((-reduced+7)/8);
    a=add8(a,(uint8_t)reduced);
    pressure_trace("B5F2",a);
    SYS_RUN(pcm_read8(pcm,0xd9,&gear));
    SYS_RUN(pcm_read16(pcm,0xb991u+(uint8_t)(gear<<1),&table));
    if(table) {
        SYS_RUN(pcm_read8(pcm,0xb5,&temp));
        SYS_RUN(temperature_column(pcm,&col));
        SYS_RUN(egr_surface(pcm,(uint8_t)(((uint16_t)temp*160u)>>8),col,table,&v));
        a=add8(a,(uint8_t)(v-128u));
    }
    pressure_trace("B680",a);
    SYS_RUN(closure_pressure_shape(pcm,&shape));
    a=add8(a,(uint8_t)(shape>>8));
    pressure_trace("B68C",a);
    SYS_RUN(pcm_pressure_shift_reduction(pcm,a,&a));
    pressure_trace("B68F",a);
    SYS_RUN(test(pcm,0x83,0x10,&set));
    if(set) {
        SYS_RUN(pcm_read8(pcm,0xd9,&index));
        SYS_RUN(pattern_index(pcm,&index));
        SYS_RUN(pcm_read16(pcm,0xb97fu+index,&table));
        if(table) {
            SYS_RUN(pcm_read8(pcm,0xd7,&v));
            SYS_RUN(pcm_read8(pcm,table,&b));
            v=v<b?0:(uint8_t)(v-b);
            SYS_RUN(pcm_read8(pcm,table+1u,&b));
            if(v>b) v=b;
            SYS_RUN(sys_curve16(pcm,v,table+2u,&v));
            a=add8(a,(uint8_t)(v-128u));
        }
    }
    pressure_trace("B6B9",a);
    SYS_RUN(pcm_pressure_modifiers(pcm,a,&a));
    pressure_trace("B6BC",a);
    SYS_RUN(down_snapshot(pcm,&gear));
    index=(uint8_t)(gear-1u);
    v=0;
    if(!(index&128u)) {
        SYS_RUN(pcm_read16(pcm,0xb999u+(uint8_t)(index<<1),&table));
        if(table) SYS_RUN(curve(pcm,table,0xb2,&v));
    }
    pressure_trace("B6D6",v);
    SYS_RUN(pressure_baro(pcm,v,&a));
    pressure_trace("B6E8",a);
    SYS_RUN(pcm_write8(pcm,0x142,a));
    SYS_RUN(speed_floor(pcm,&a));
    SYS_RUN(engagement(pcm,&a));
    SYS_RUN(test(pcm,0x9c,2,&set));
    if(set) {
        SYS_RUN(pcm_read8(pcm,0xd9,&gear));
        SYS_RUN(pcm_read8(pcm,0x5f21u+gear,&v));
        a=sub8(a,v);
        if(a&128u) a=0;
    }
    SYS_RUN(pcm_read8(pcm,0x5f2c,&cap));
    /* B855 SBA; RORA/ROLA reconstruct A and set V=N xor carry. */
    { uint8_t diff=(uint8_t)(cap-a); bool borrow=cap<a;
      bool overflow=((diff&128u)!=0)!=borrow;
      v=overflow?(uint8_t)(127u+borrow):diff; }
    SYS_RUN(pcm_read8(pcm,0xe0,&b));
    if(s8(v)<s8(b)) SYS_RUN(pcm_write8(pcm,0xe0,v));
    SYS_RUN(pcm_read8(pcm,0xdf,&b));
    if(s8(a)<s8(b)) SYS_RUN(pcm_write8(pcm,0xdf,a));
    SYS_RUN(test(pcm,0x98,8,&set));
    if(!set) {
        SYS_RUN(pcm_transmission_fault_gate_664(pcm));
        SYS_RUN(test(pcm,0x98,0x20,&set));
    }
    if(set||cap<a) a=cap;
    SYS_RUN(pcm_read8(pcm,0x112,&v));
    a=add8(a,v);
    if(a&128u) a=0;
    return pcm_write8(pcm,0xe2,a);
}
static PcmStatus descriptor(Pcm *pcm,uint16_t table,uint16_t fallback,uint16_t *ptr)
{
    uint8_t gear,selector;
    bool valid;
    SYS_RUN(pcm_read8(pcm,0x7f,&selector));
    SYS_RUN(pcm_read8(pcm,0xd9,&gear));
    SYS_RUN(pcm_transmission_descriptor(pcm,table,selector,gear,ptr,&valid));
    if(!valid) *ptr=fallback;
    return PCM_OK;
}
static PcmStatus base_curve(Pcm *pcm,uint16_t table,uint16_t fallback,uint16_t pair)
{
    uint16_t ptr;
    SYS_RUN(descriptor(pcm,table,fallback,&ptr));
    return pcm_tcc_base_curve(pcm,ptr,pair);
}
static PcmStatus rate(Pcm *pcm,bool release,uint8_t *v)
{
    uint16_t ptr;
    SYS_RUN(pcm_read8(pcm,0x110,v));
    if(*v) return PCM_OK;
    if(release) {
        SYS_RUN(pcm_read8(pcm,0x18e,v));
        if(*v) return pcm_read8(pcm,0x6ade,v);
    }
    SYS_RUN(descriptor(pcm,release?0xc3c4:0xc3a2,release?0x6d1a:0x6e08,&ptr));
    return curve(pcm,ptr,0xb2,v);
}
static PcmStatus clear_tcc(Pcm *pcm,bool preserve_hold)
{
    if(!preserve_hold) SYS_RUN(pcm_write16(pcm,0x11f,0));
    SYS_RUN(pcm_update8(pcm,0x89,0x70,0));
    SYS_RUN(pcm_update8(pcm,0x8a,0x40,0));
    return pcm_write16(pcm,0x126,0);
}
static PcmStatus tcc_tail(Pcm *pcm)
{
    uint16_t d,f,limit;
    SYS_RUN(pcm_read16(pcm,0x12b,&d));
    SYS_RUN(pcm_read16(pcm,0xf3,&f));
    if(d<f) {
        SYS_RUN(pcm_read16(pcm,0x129,&d));
        SYS_RUN(pcm_read16(pcm,0xf3,&f));
        if(d>f) SYS_RUN(pcm_read16(pcm,0xf3,&d));
    }
    SYS_RUN(pcm_write16(pcm,0x126,d));
    SYS_RUN(pcm_read16(pcm,0xf1,&limit));
    uint16_t delta=(uint16_t)(d-limit);
    uint8_t a=(uint8_t)(delta>>8);
    bool c=(a&1u)!=0;
    a=(uint8_t)((a>>1)|(d<limit?128u:0));
    a=a==127u&&c?127u:(uint8_t)(a+c);
    return pcm_write8(pcm,0xe9,a);
}
static PcmStatus command_delta(Pcm *pcm,uint8_t rate_,bool release,uint16_t *out,bool *carry)
{
    uint16_t d=(uint16_t)rate_*8u;
    uint8_t a=(uint8_t)(d>>8),b=(uint8_t)d,old,high;
    SYS_RUN(pcm_write8(pcm,0x18f,a));
    SYS_RUN(pcm_read8(pcm,0x18f,&old));
    b=(uint8_t)(b+old);
    SYS_RUN(pcm_read8(pcm,0x127,&old));
    if(release) {
        bool borrow=b<old;
        b=(uint8_t)(b-old);
        if(borrow) --b;
        SYS_RUN(pcm_read8(pcm,0x126,&high));
        unsigned sub=(unsigned)high+borrow;
        *carry=a<sub;
        a=(uint8_t)(a-sub);
    } else {
        unsigned sum=(unsigned)b+old;
        b=(uint8_t)sum;
        bool c=sum>255u;
        if(c) ++b;
        SYS_RUN(pcm_read8(pcm,0x126,&high));
        sum=(unsigned)a+high+c;
        *carry=sum>255u;
        a=(uint8_t)sum;
    }
    *out=(uint16_t)(((uint16_t)a<<8)|b);
    return PCM_OK;
}
static PcmStatus converge(Pcm *pcm)
{
    SYS_RUN(copy8(pcm,0x12d,0xe6));
    SYS_RUN(pcm_update8(pcm,0x89,0,0x20));
    SYS_RUN(pcm_tcc_base_curve(pcm,0x6e3b,0x10f));
    SYS_RUN(pcm_write8(pcm,0xf6,0));
    SYS_RUN(pcm_write8(pcm,0x12d,0));
    SYS_RUN(copy8(pcm,0x6e4c,0xea));
    SYS_RUN(copy8(pcm,0x6e51,0xf5));
    return tcc_tail(pcm);
}
static PcmStatus apply_converged(Pcm *pcm)
{
    bool set;
    uint8_t age,v,a,b;
    uint16_t d,slip,limit;
    SYS_RUN(test(pcm,0x83,3,&set));
    if(set) {
        SYS_RUN(test(pcm,0xa2,4,&set));
        if(set) {
            SYS_RUN(pcm_read8(pcm,0xd9,&v));
            set=v==3;
        }
        if(!set) return copy16(pcm,0x129,0x126);
    }
    SYS_RUN(pcm_tcc_base_curve(pcm,0x6e3b,0x10f));
    SYS_RUN(pcm_read8(pcm,0xea,&age));
    if(age) --age;
    else {
        SYS_RUN(pcm_read8(pcm,0x6e4c,&age));
        if(age) {
            SYS_RUN(pcm_read8(pcm,0xe9,&a));
            SYS_RUN(pcm_read8(pcm,0x6e4d,&b));
            SYS_RUN(pcm_write8(pcm,0xe9,add8(a,b)));
        }
    }
    SYS_RUN(pcm_write8(pcm,0xea,age));
    SYS_RUN(pcm_read16(pcm,0xed,&slip));
    SYS_RUN(pcm_read8(pcm,0xf5,&age));
    if(age) SYS_RUN(pcm_write8(pcm,0xf5,(uint8_t)(age-1u)));
    else {
        SYS_RUN(pcm_read16(pcm,0x6e4e,&limit));
        if(slip>limit) {
            SYS_RUN(pcm_read8(pcm,0xe9,&a));
            SYS_RUN(pcm_read8(pcm,0x6e50,&b));
            SYS_RUN(pcm_write8(pcm,0xe9,add8(a,b)));
            SYS_RUN(copy8(pcm,0x6e51,0xf5));
        }
    }
    SYS_RUN(pcm_read8(pcm,0xf6,&age));
    ++age;
    SYS_RUN(pcm_read16(pcm,0x6e52,&limit));
    if(slip<limit) age=0;
    SYS_RUN(pcm_write8(pcm,0xf6,age));
    SYS_RUN(pcm_read8(pcm,0xf1,&a));
    d=(uint16_t)(((uint16_t)a<<8)|age);
    d>>=1;
    SYS_RUN(pcm_read8(pcm,0xe9,&v));
    a=(uint8_t)(add8((uint8_t)((d>>8)-128u),v)+128u);
    d=(uint16_t)(((uint16_t)a<<8)|(uint8_t)d);
    bool carry=(d&0x8000u)!=0;
    d=(uint16_t)(d<<1);
    SYS_RUN(pcm_read8(pcm,0xf2,&b));
    d=carry?UINT16_MAX:(uint16_t)((d&0xff00u)|b);
    SYS_RUN(pcm_write16(pcm,0xf3,d));
    return tcc_tail(pcm);
}
static PcmStatus apply(Pcm *pcm)
{
    bool set,carry;
    uint16_t d,limit,slip;
    uint8_t v;
    SYS_RUN(test(pcm,0x87,2,&set));
    if(!set) {
        SYS_RUN(test(pcm,0x8b,0x80,&set));
        if(set) {
            SYS_RUN(pcm_read16(pcm,0x11f,&d));
            SYS_RUN(pcm_read16(pcm,0x121,&limit));
            if(d<limit) {
                SYS_RUN(pcm_update8(pcm,0x8b,0,0x40));
                SYS_RUN(pcm_write16(pcm,0x11f,d==UINT16_MAX?d:(uint16_t)(d+1u)));
                return clear_tcc(pcm,true);
            }
            SYS_RUN(pcm_update8(pcm,0x8b,0x80,0));
        }
    }
    SYS_RUN(pcm_write16(pcm,0x11f,0));
    SYS_RUN(pcm_update8(pcm,0x8b,0x40,0));
    SYS_RUN(test(pcm,0x89,0x40,&set));
    if(!set) {
        SYS_RUN(pcm_update8(pcm,0x8b,0,0x10));
        SYS_RUN(pcm_update8(pcm,0x89,0,0x40));
        SYS_RUN(pcm_update8(pcm,0x89,0x10,0));
        SYS_RUN(pcm_write8(pcm,0x125,0));
        SYS_RUN(pcm_write8(pcm,0x12d,0));
        SYS_RUN(pcm_write8(pcm,0x12e,0));
        SYS_RUN(copy8(pcm,0x6add,0xe7));
    }
    SYS_RUN(test(pcm,0x89,0x20,&set));
    if(set) return apply_converged(pcm);
    SYS_RUN(base_curve(pcm,0xc35e,0x6db3,0x10b));
    SYS_RUN(rate(pcm,false,&v));
    SYS_RUN(command_delta(pcm,v,false,&d,&carry));
    if(carry) d=UINT16_MAX;
    SYS_RUN(pcm_read16(pcm,0xf1,&limit));
    if(d<limit) SYS_RUN(pcm_read16(pcm,0xf1,&d));
    SYS_RUN(pcm_write16(pcm,0xf3,d));
    SYS_RUN(pcm_read16(pcm,0xed,&slip));
    SYS_RUN(pcm_read16(pcm,0x6ad9,&limit));
    if(slip>limit) SYS_RUN(pcm_write8(pcm,0xe7,1));
    else {
        SYS_RUN(pcm_read16(pcm,0x6adb,&limit));
        if(slip<limit) {
            SYS_RUN(pcm_read8(pcm,0xe7,&v));
            --v; SYS_RUN(pcm_write8(pcm,0xe7,v));
            if(!v) return converge(pcm);
        }
    }
    SYS_RUN(pcm_read16(pcm,0xf3,&d));
    SYS_RUN(pcm_read16(pcm,0x129,&limit));
    return d>=limit?converge(pcm):tcc_tail(pcm);
}
static PcmStatus release(Pcm *pcm)
{
    bool set,borrow;
    uint8_t v,age;
    uint16_t d,limit;
    SYS_RUN(test(pcm,0x89,0x40,&set));
    if(set) {
        SYS_RUN(pcm_update8(pcm,0x89,0,0x10));
        SYS_RUN(pcm_update8(pcm,0x89,0x60,0));
        SYS_RUN(pcm_update8(pcm,0x8a,0x40,0));
        SYS_RUN(pcm_write16(pcm,0x11f,0));
        SYS_RUN(pcm_write8(pcm,0x12d,0));
        SYS_RUN(pcm_write8(pcm,0x12e,0));
    } else {
        SYS_RUN(test(pcm,0x89,0x10,&set));
        if(!set) return clear_tcc(pcm,false);
    }
    SYS_RUN(base_curve(pcm,0xc380,0x6cc5,0x10c));
    SYS_RUN(rate(pcm,true,&v));
    SYS_RUN(command_delta(pcm,v,true,&d,&borrow));
    if(!borrow) return clear_tcc(pcm,false);
    d=(uint16_t)(0u-d);
    SYS_RUN(pcm_read16(pcm,0xf1,&limit));
    if(d>limit) SYS_RUN(pcm_read16(pcm,0xf1,&d));
    SYS_RUN(pcm_write16(pcm,0xf3,d));
    SYS_RUN(pcm_read16(pcm,0x12b,&d));
    SYS_RUN(pcm_read16(pcm,0xf3,&limit));
    if(d>limit) return clear_tcc(pcm,false);
    SYS_RUN(test(pcm,0x8a,0x40,&set));
    if(!set) {
        SYS_RUN(pcm_read16(pcm,0xed,&d));
        SYS_RUN(pcm_read16(pcm,0x6adf,&limit));
        if(d<=limit) {
            SYS_RUN(pcm_read8(pcm,0x10d,&v));
            if(!v) SYS_RUN(curve(pcm,0x6d3c,0xb2,&v));
            SYS_RUN(pcm_read8(pcm,0x12d,&age));
            return v>=age?tcc_tail(pcm):clear_tcc(pcm,false);
        }
        SYS_RUN(copy8(pcm,0x12d,0xe5));
        SYS_RUN(pcm_update8(pcm,0x8a,0,0x40));
    }
    SYS_RUN(pcm_read8(pcm,0x10e,&v));
    if(!v) SYS_RUN(curve(pcm,0x6d4d,0xb2,&v));
    SYS_RUN(pcm_read8(pcm,0x12d,&age));
    return v>=age?tcc_tail(pcm):clear_tcc(pcm,false);
}
PcmStatus closure_tcc_command(Pcm *pcm)
{
    bool set;
    SYS_RUN(test(pcm,0x8a,0x10,&set));
    if(set) return PCM_OK;
    SYS_RUN(test(pcm,0x8b,4,&set));
    if(set) return apply(pcm);
    SYS_RUN(test(pcm,0x8b,2,&set));
    return set?release(pcm):clear_tcc(pcm,false);
}
/* B56B dispatches only when both calibration bits are clear. */
PcmStatus closure_pressure_group(Pcm *pcm)
{
    bool set;
    SYS_RUN(test(pcm,0x400f,0xc0,&set));
    if(set) return PCM_OK;
    SYS_RUN(closure_pressure_main(pcm));
    SYS_RUN(pcm_pressure_current_reference(pcm));
    SYS_RUN(pcm_pressure_learning_count(pcm));
    SYS_RUN(pcm_tcc_event_timers(pcm));
    SYS_RUN(pcm_tcc_throttle_events(pcm));
    return closure_tcc_command(pcm);
}
