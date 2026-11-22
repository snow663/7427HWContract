#include "diagnostic_internal.h"
/* F0AD..F130, code87: high-gear ratio floor, temperature and recovery budget. */
PcmStatus pcm_diagnostic_ratio_highgear(Pcm *pcm)
{
    uint8_t a,b,flags,limit;uint16_t sample,threshold;
    if (pcm->runtime.monitor_freeze) return PCM_OK;
    DG8(0x5b08,flags);if (!(flags&0x10u)) goto reset;
    DG8(0x181,a);DG8(0x96,flags);if (flags&0x20u) goto test;
    DG_SET(0x96,0x20);DG8(0x1e,flags);if (!(flags&0x10u)) goto reset;
    DG8(0x30,b);DG8(0x5bc0,limit);if (b>=limit) goto reset;
    SYS_RUN(pcm_serial_memory_write8(pcm,0x30,(uint8_t)(b+2u)));DG_CLEAR(0x1e,0x10);goto reset;
test:
    DG8(0x1e,flags);if (flags&0x10u) goto reset;
    DG8(0xd9,b);if (b<2) goto reset;
    DG16(0xf9,sample);DG16(0x5bb3,threshold);if (sample<threshold) goto reset;
    DG8(0x16,flags);if (flags&1u) goto reset;
    DG8(0x17,flags);if (flags&0x80u) goto reset;
    DG8(0xb2,b);DG8(0x5bac,limit);if (b<=limit) goto reset;
    DG8(0xb5,b);DG8(0x5bae,limit);if (b<=limit) goto reset;
    DG8(0x1c,flags);if (flags&8u) goto reset;
    DG16(0x1ac,sample);DG16(0x5b84,threshold);if (sample<=threshold) goto reset;
    DG8(0x17,flags);if (flags&0x20u) goto reset;
    DG8(0x1c,flags);if (flags&4u) goto reset;
    DG8(0x1c,flags);if (flags&1u) goto reset;
    DG8(0xd7,b);DG8(0x5bad,limit);if (b<=limit) goto reset;
    DG8(0x17,flags);if (flags&2u) goto reset;
    DG8(0xa2,flags);if (!(flags&0x0fu)) goto reset;
    a=(uint8_t)(a+1u);DG8(0x5bbf,limit);if (a<limit) goto store;
    DG_SET(0x1e,0x10);
reset:a=0;
store:return pcm_serial_memory_write8(pcm,0x181,a);
}
