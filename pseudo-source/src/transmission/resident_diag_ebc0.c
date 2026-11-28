#include "resident_input_private_2.h"
static const Diagnostic output_speed={0x5b06,0x1c,0x95,0x175,0x5b8d,0x29,0x5b8c,4,0x10};

PcmStatus pcm_resident_diag_ebc0(Pcm *pcm)
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
