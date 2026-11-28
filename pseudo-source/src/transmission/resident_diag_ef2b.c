#include "resident_input_private_2.h"
static const Diagnostic turbine_speed={0x5b06,0x1c,0,0x177,0x5b95,0,0,1,0};

PcmStatus pcm_resident_diag_ef2b(Pcm *pcm)
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
    if(set) return zero_timer(pcm,d);
    SYS_RUN(pcm_read16(pcm,0x1ac,&sample));
    SYS_RUN(pcm_read16(pcm,0x5b84,&bound)); if(sample<=bound) return zero_timer(pcm,d);
    SYS_RUN(test_bits(pcm,0x17,2,&set)); if(set) return zero_timer(pcm,d);
    return qualify(pcm,d,age,true);
}
