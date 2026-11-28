#include "resident_input_private_2.h"
static const Diagnostic vehicle_speed={0x5b01,0x17,0x94,0x164,0x5b41,0x21,0x5b42,0x20,4};

/* E847: the first latch observation enters recovery, before testing
 * the vehicle speed admission conditions. */
PcmStatus pcm_resident_diag_e847(Pcm *pcm)
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
