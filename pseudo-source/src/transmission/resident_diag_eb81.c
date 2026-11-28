#include "resident_input_private_2.h"
static const Diagnostic engine_speed={0x5b06,0x1c,0,0x174,0x5b83,0,0,8,0};

/* EB81 and EF2B use time-qualified recovery rather than an edge latch. */
PcmStatus pcm_resident_diag_eb81(Pcm *pcm)
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
