#ifndef PCM_RESIDENT_INPUT_PRIVATE_2
#define PCM_RESIDENT_INPUT_PRIVATE_2
#include "resident_transmission.h"
#include "reference_math.h"
#include "../system/system_internal.h"
typedef struct {
    uint16_t enable, live, latch, timer, limit, count, recovery;
    uint8_t bit, latch_bit;
} Diagnostic;
static inline PcmStatus test_bits(Pcm *pcm, uint16_t address, uint8_t mask, bool *set)
{
    uint8_t value;
    SYS_RUN(pcm_read8(pcm,address,&value));
    *set=(value&mask)!=0;
    return PCM_OK;
}

/* The monitor freeze returns without touching the timer. A disabled
 * calibration mask, in contrast, clears it. */
static inline PcmStatus admission(Pcm *pcm,const Diagnostic *d,bool *frozen,bool *enabled)
{
    SYS_RUN(test_bits(pcm,0x3b,4,frozen));
    if (*frozen) { *enabled=false; return PCM_OK; }
    return test_bits(pcm,d->enable,d->bit,enabled);
}

static inline PcmStatus zero_timer(Pcm *pcm,const Diagnostic *d)
{
    return pcm_write8(pcm,d->timer,0);
}

static inline PcmStatus qualify(Pcm *pcm,const Diagnostic *d,uint8_t age,bool set)
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
static inline PcmStatus recover(Pcm *pcm,const Diagnostic *d)
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

static inline PcmStatus set_if_new(Pcm *pcm,const Diagnostic *d,uint8_t age)
{
    bool set;
    SYS_RUN(test_bits(pcm,d->live,d->bit,&set));
    return set?zero_timer(pcm,d):qualify(pcm,d,age,true);
}

static inline PcmStatus tps_monitor(Pcm *pcm,const Diagnostic *d,uint16_t threshold,bool high)
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

static inline PcmStatus pattern_monitor(Pcm *pcm,const Diagnostic *d,uint16_t source,uint8_t mask)
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

/* EBC0: N selects NEGB; NEGA; SBCA #0. NEGA supplies carry to
 * SBCA, including when the original low byte is zero. This is NOT abs(). */
static inline uint16_t n_magnitude(uint16_t value)
{
    if(!(value&0x8000u)) return value;
    uint8_t hi=(uint8_t)(value>>8),lo=(uint8_t)value;
    uint8_t neg_hi=(uint8_t)(0u-hi-(hi!=0));
    return (uint16_t)((uint16_t)neg_hi<<8)|(uint8_t)(0u-lo);
}

#endif
