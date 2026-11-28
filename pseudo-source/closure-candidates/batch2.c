#include "batch2.h"
#include "../src/system/system_internal.h"

typedef struct {
    uint16_t enable, live, latch, timer, limit, count, recovery;
    uint8_t bit, latch_bit;
} Diagnostic;

static PcmStatus test_bits(Pcm *pcm, uint16_t address, uint8_t mask, bool *set)
{
    uint8_t value;
    SYS_RUN(pcm_read8(pcm,address,&value));
    *set=(value&mask)!=0;
    return PCM_OK;
}

/* The monitor freeze returns without touching the timer. A disabled
 * calibration mask, in contrast, clears it. */
static PcmStatus admission(Pcm *pcm,const Diagnostic *d,bool *frozen,bool *enabled)
{
    SYS_RUN(test_bits(pcm,0x3b,4,frozen));
    if (*frozen) { *enabled=false; return PCM_OK; }
    return test_bits(pcm,d->enable,d->bit,enabled);
}
static PcmStatus zero_timer(Pcm *pcm,const Diagnostic *d)
{
    return pcm_write8(pcm,d->timer,0);
}
static PcmStatus qualify(Pcm *pcm,const Diagnostic *d,uint8_t age,bool set)
{
    uint8_t limit;
    age=(uint8_t)(age+1u);
    SYS_RUN(pcm_read8(pcm,d->limit,&limit));
    if(age>=limit) {
        SYS_RUN(pcm_update8(pcm,d->live,set?0:d->bit,set?d->bit:0));
        age=0;
    }
    return pcm_write8(pcm,d->timer,age);
}
/* Once-per-cycle recovery latch. The count comparison is unsigned;
 * the two increments wrap as byte operations. A zero count address
 * denotes the ECCC path, which clears without a count test. */
static PcmStatus recover(Pcm *pcm,const Diagnostic *d)
{
    bool set;
    SYS_RUN(test_bits(pcm,d->latch,d->latch_bit,&set));
    if(set) return zero_timer(pcm,d);
    SYS_RUN(pcm_update8(pcm,d->latch,0,d->latch_bit));
    SYS_RUN(test_bits(pcm,d->live,d->bit,&set));
    if(set) {
        if(d->count) {
            uint8_t count,limit;
            SYS_RUN(pcm_read8(pcm,d->count,&count));
            SYS_RUN(pcm_read8(pcm,d->recovery,&limit));
            if(count>=limit) return zero_timer(pcm,d);
            SYS_RUN(pcm_write8(pcm,d->count,(uint8_t)(count+2u)));
        }
        SYS_RUN(pcm_update8(pcm,d->live,d->bit,0));
    }
    return zero_timer(pcm,d);
}
static PcmStatus set_if_new(Pcm *pcm,const Diagnostic *d,uint8_t age)
{
    bool set;
    SYS_RUN(test_bits(pcm,d->live,d->bit,&set));
    return set?zero_timer(pcm,d):qualify(pcm,d,age,true);
}
static const Diagnostic high_tps={0x5b00,0x16,0x94,0x162,0x5b1d,0x1f,0x5b1e,1,1};
static const Diagnostic low_tps={0x5b01,0x17,0x94,0x163,0x5b20,0x20,0x5b21,0x80,2};
static const Diagnostic vehicle_speed={0x5b01,0x17,0x94,0x164,0x5b41,0x21,0x5b42,0x20,4};
static const Diagnostic range_pattern={0x5b01,0x17,0x94,0x165,0x5b51,0x22,0x5b52,2,8};
static const Diagnostic engine_speed={0x5b06,0x1c,0,0x174,0x5b83,0,0,8,0};
static const Diagnostic output_speed={0x5b06,0x1c,0x95,0x175,0x5b8d,0x29,0x5b8c,4,0x10};
static const Diagnostic request_pattern={0x5b07,0x1d,0x95,0x179,0x5b9d,0,0,0x20,0x40};
static const Diagnostic turbine_speed={0x5b06,0x1c,0,0x177,0x5b95,0,0,1,0};

static PcmStatus tps_monitor(Pcm *pcm,const Diagnostic *d,uint16_t threshold,bool high)
{
    bool frozen,enabled;
    uint8_t age,tps,limit;
    SYS_RUN(admission(pcm,d,&frozen,&enabled));
    if(frozen) return PCM_OK;
    if(!enabled) return zero_timer(pcm,d);
    SYS_RUN(pcm_read8(pcm,d->timer,&age));
    SYS_RUN(pcm_read8(pcm,0xa6,&tps));
    SYS_RUN(pcm_read8(pcm,threshold,&limit));
    bool fault=high?tps>limit:tps<limit;
    return fault?set_if_new(pcm,d,age):recover(pcm,d);
}
PcmStatus closure_diag_e7c7(Pcm *pcm) { return tps_monitor(pcm,&high_tps,0x5b1c,true); }
PcmStatus closure_diag_e808(Pcm *pcm) { return tps_monitor(pcm,&low_tps,0x5b1f,false); }

/* E847: the first latch observation enters recovery, before testing
 * the vehicle speed admission conditions. */
PcmStatus closure_diag_e847(Pcm *pcm)
{
    const Diagnostic *d=&vehicle_speed;
    bool frozen,enabled,set;
    uint8_t age,value,limit;
    uint16_t sample,bound;
    SYS_RUN(admission(pcm,d,&frozen,&enabled));
    if(frozen) return PCM_OK;
    if(!enabled) return zero_timer(pcm,d);
    SYS_RUN(pcm_read8(pcm,d->timer,&age));
    SYS_RUN(test_bits(pcm,d->latch,d->latch_bit,&set));
    if(!set) return recover(pcm,d);
    SYS_RUN(test_bits(pcm,0x17,0x20,&set)); if(set) return zero_timer(pcm,d);
    SYS_RUN(test_bits(pcm,0x18,0x20,&set)); if(set) return zero_timer(pcm,d);
    SYS_RUN(test_bits(pcm,0x18,0x10,&set)); if(set) return zero_timer(pcm,d);
    SYS_RUN(test_bits(pcm,0x16,1,&set)); if(set) return zero_timer(pcm,d);
    SYS_RUN(test_bits(pcm,0x17,0x80,&set)); if(set) return zero_timer(pcm,d);
    SYS_RUN(pcm_read8(pcm,0x1c0,&value));
    SYS_RUN(pcm_read8(pcm,0x5b45,&limit)); if(value<limit) return zero_timer(pcm,d);
    SYS_RUN(pcm_read8(pcm,0x5b46,&limit)); if(value>limit) return zero_timer(pcm,d);
    SYS_RUN(pcm_read8(pcm,0xb2,&value));
    SYS_RUN(pcm_read8(pcm,0x5b47,&limit)); if(value<limit) return zero_timer(pcm,d);
    SYS_RUN(pcm_read8(pcm,0x5b48,&limit)); if(value>limit) return zero_timer(pcm,d);
    SYS_RUN(pcm_read16(pcm,0xd1,&sample));
    SYS_RUN(pcm_read16(pcm,0x5b3d,&bound)); if(sample>=bound) return zero_timer(pcm,d);
    SYS_RUN(test_bits(pcm,0x1c,1,&set)); if(set) return zero_timer(pcm,d);
    SYS_RUN(test_bits(pcm,0x17,2,&set)); if(set) return zero_timer(pcm,d);
    SYS_RUN(pcm_read16(pcm,0xc2,&sample));
    SYS_RUN(pcm_read16(pcm,0x5b3f,&bound)); if(sample<=bound) return zero_timer(pcm,d);
    SYS_RUN(test_bits(pcm,0xa2,0x50,&set)); if(set) return zero_timer(pcm,d);
    return qualify(pcm,d,age,true);
}

static PcmStatus pattern_monitor(Pcm *pcm,const Diagnostic *d,uint16_t source,uint8_t mask)
{
    bool frozen,enabled,set;
    uint8_t age;
    SYS_RUN(admission(pcm,d,&frozen,&enabled));
    if(frozen) return PCM_OK;
    if(!enabled) return zero_timer(pcm,d);
    SYS_RUN(pcm_read8(pcm,d->timer,&age));
    SYS_RUN(test_bits(pcm,source,mask,&set));
    return set?set_if_new(pcm,d,age):recover(pcm,d);
}
PcmStatus closure_diag_e8c8(Pcm *pcm) { return pattern_monitor(pcm,&range_pattern,0xa2,0x80); }
PcmStatus closure_diag_eccc(Pcm *pcm) { return pattern_monitor(pcm,&request_pattern,0x9f,8); }

/* EB81 and EF2B use time-qualified recovery rather than an edge latch. */
PcmStatus closure_diag_eb81(Pcm *pcm)
{
    const Diagnostic *d=&engine_speed;
    bool frozen,enabled,set;
    uint8_t age;
    uint16_t sample,bound;
    SYS_RUN(admission(pcm,d,&frozen,&enabled));
    if(frozen) return PCM_OK;
    if(!enabled) return zero_timer(pcm,d);
    SYS_RUN(pcm_read8(pcm,d->timer,&age));
    SYS_RUN(pcm_read16(pcm,0xb7,&sample));
    SYS_RUN(pcm_read16(pcm,0x5b81,&bound));
    SYS_RUN(test_bits(pcm,d->live,d->bit,&set));
    if(sample>=bound) return set?qualify(pcm,d,age,false):zero_timer(pcm,d);
    if(set) return zero_timer(pcm,d);
    SYS_RUN(test_bits(pcm,0x17,2,&set)); if(set) return zero_timer(pcm,d);
    SYS_RUN(test_bits(pcm,0xa2,0x52,&set)); if(set) return zero_timer(pcm,d);
    return qualify(pcm,d,age,true);
}

/* EBC0: N selects NEGB; NEGA; SBCA #0. NEGA supplies carry to
 * SBCA, including when the original low byte is zero. This is NOT abs(). */
static uint16_t n_magnitude(uint16_t value)
{
    if(!(value&0x8000u)) return value;
    uint8_t hi=(uint8_t)(value>>8),lo=(uint8_t)value;
    uint8_t neg_hi=(uint8_t)(0u-hi-(hi!=0));
    return (uint16_t)((uint16_t)neg_hi<<8)|(uint8_t)(0u-lo);
}
PcmStatus closure_diag_ebc0(Pcm *pcm)
{
    const Diagnostic *d=&output_speed;
    bool frozen,enabled,set;
    uint8_t age;
    uint16_t a,b,limit;
    SYS_RUN(admission(pcm,d,&frozen,&enabled));
    if(frozen) return PCM_OK;
    if(!enabled) return zero_timer(pcm,d);
    SYS_RUN(pcm_read16(pcm,0xd5,&a));
    SYS_RUN(pcm_read16(pcm,0xcc,&b));
    uint16_t magnitude=n_magnitude((uint16_t)(a-b));
    SYS_RUN(test_bits(pcm,0xa2,0x50,&set));
    SYS_RUN(pcm_read16(pcm,set?0x5b88:0x5b86,&limit));
    if(magnitude<=limit) return recover(pcm,d);
    SYS_RUN(test_bits(pcm,d->live,d->bit,&set)); if(set) return zero_timer(pcm,d);
    SYS_RUN(test_bits(pcm,0x1ab,0xff,&set)); if(set) return zero_timer(pcm,d);
    SYS_RUN(pcm_read16(pcm,0x1ac,&a));
    SYS_RUN(pcm_read16(pcm,0x5b8a,&limit)); if(a<limit) return zero_timer(pcm,d);
    SYS_RUN(pcm_read8(pcm,0xa1,&age)); if(age!=255u) return zero_timer(pcm,d);
    SYS_RUN(test_bits(pcm,0x17,2,&set)); if(set) return zero_timer(pcm,d);
    SYS_RUN(pcm_read8(pcm,d->timer,&age));
    return qualify(pcm,d,age,true);
}
PcmStatus closure_diag_ef2b(Pcm *pcm)
{
    const Diagnostic *d=&turbine_speed;
    bool frozen,enabled,set;
    uint8_t age;
    uint16_t sample,bound;
    SYS_RUN(admission(pcm,d,&frozen,&enabled));
    if(frozen) return PCM_OK;
    if(!enabled) return zero_timer(pcm,d);
    SYS_RUN(pcm_read8(pcm,d->timer,&age));
    SYS_RUN(pcm_read16(pcm,0xbd,&sample));
    SYS_RUN(pcm_read16(pcm,0x5b91,&bound));
    SYS_RUN(test_bits(pcm,d->live,d->bit,&set));
    if(sample>=bound) return set?qualify(pcm,d,age,false):zero_timer(pcm,d);
    if(set) return zero_timer(pcm,d);
    SYS_RUN(test_bits(pcm,0xa2,0x50,&set)); if(set) return zero_timer(pcm,d);
    SYS_RUN(test_bits(pcm,0x17,0x20,&set)); if(set) return zero_timer(pcm,d);
    SYS_RUN(test_bits(pcm,0x1c,4,&set)); if(set) return zero_timer(pcm,d);
    SYS_RUN(pcm_read16(pcm,0xd3,&sample));
    SYS_RUN(pcm_read16(pcm,0x5b93,&bound)); if(sample<=bound) return zero_timer(pcm,d);
    SYS_RUN(test_bits(pcm,0x1c,8,&set));
    if(!set) {
        SYS_RUN(pcm_read16(pcm,0x1ac,&sample));
        SYS_RUN(pcm_read16(pcm,0x5b84,&bound)); if(sample<=bound) return zero_timer(pcm,d);
    }
    SYS_RUN(test_bits(pcm,0x17,2,&set)); if(set) return zero_timer(pcm,d);
    return qualify(pcm,d,age,true);
}
