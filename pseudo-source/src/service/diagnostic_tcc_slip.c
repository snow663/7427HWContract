#include "diagnostic_internal.h"
/* EE02..EE5E, code39: signed slip, first observation and recovery budget. */
PcmStatus pcm_diagnostic_tcc_slip(Pcm *pcm)
{
    uint8_t a,b,flags,limit;uint16_t sample,threshold;
    if (pcm->runtime.monitor_freeze) return PCM_OK;
    DG8(0x5b03,flags);if (!(flags&0x80u)) goto reset;
    DG8(0x168,a);DG8(0x95,flags);if (flags&1u) goto test;
    DG_SET(0x95,1);DG8(0x19,flags);if (!(flags&0x80u)) goto reset;
    DG8(0x25,b);DG8(0x5b62,limit);if (b>=limit) goto reset;
    SYS_RUN(pcm_serial_memory_write8(pcm,0x25,(uint8_t)(b+2u)));DG_CLEAR(0x19,0x80);goto reset;
test:
    DG8(0x19,flags);if (flags&0x80u) goto reset;
    DG16(0xeb,sample);DG16(0x5b5f,threshold);if (dg_signed(sample)<dg_signed(threshold)) goto reset;
    DG8(0x89,flags);if (!(flags&0x20u)) goto reset;
    DG8(0xd9,b);if (b==0 || b==3) goto reset;
    DG8(0x1c,flags);if (flags&8u) goto reset;
    DG8(0x1c,flags);if (flags&1u) goto reset;
    DG8(0x17,flags);if (flags&2u) goto reset;
    DG8(0xa2,flags);if (!(flags&0x0cu)) goto reset;
    a=(uint8_t)(a+1u);DG8(0x5b61,limit);if (a<limit) goto store;
    DG_SET(0x19,0x80);
reset:a=0;
store:return pcm_serial_memory_write8(pcm,0x168,a);
}
