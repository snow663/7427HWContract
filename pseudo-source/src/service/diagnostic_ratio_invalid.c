#include "diagnostic_internal.h"
/* EF88..F02E, code85: exclude four open ratio windows, preserving the
 * intervening gear test and ordered input-fault admissions. */
PcmStatus pcm_diagnostic_ratio_invalid(Pcm *pcm)
{
    uint8_t a,b,flags,limit;uint16_t ratio,threshold;
    if (pcm->runtime.monitor_freeze) return PCM_OK;
    DG8(0x5b08,flags);if (!(flags&0x40u)) goto reset;
    DG8(0x17f,a);DG8(0x96,flags);if (flags&8u) goto test;
    DG_SET(0x96,8);DG8(0x1e,flags);if (!(flags&0x40u)) goto reset;
    DG8(0x2e,b);DG8(0x5ba9,limit);if (b>=limit) goto reset;
    SYS_RUN(pcm_serial_memory_write8(pcm,0x2e,(uint8_t)(b+2u)));DG_CLEAR(0x1e,0x40);goto reset;
test:
    DG16(0xf9,ratio);DG16(0x5baf,threshold);if (ratio<=threshold) goto second;
    DG16(0x5bb1,threshold);if (ratio<threshold) goto reset;
second:
    DG16(0x5bb3,threshold);if (ratio<=threshold) goto third;
    DG16(0x5bb5,threshold);if (ratio<threshold) goto reset;
third:
    DG16(0x5bb7,threshold);if (ratio<=threshold) goto fourth;
    DG16(0x5bb9,threshold);if (ratio<threshold) goto reset;
fourth:
    DG8(0xd9,b);if (b==3) goto reset;
    DG16(0x5bbb,threshold);if (ratio<=threshold) goto gates;
    DG16(0x5bbd,threshold);if (ratio<threshold) goto reset;
gates:
    DG8(0x1e,flags);if (flags&0x40u) goto reset;
    DG8(0x16,flags);if (flags&1u) goto reset;
    DG8(0x17,flags);if (flags&0x80u) goto reset;
    DG8(0x1e,flags);if (flags&0x10u) goto reset;
    DG8(0x17,flags);if (flags&2u) goto reset;
    DG8(0xb2,b);DG8(0x5bac,limit);if (b<=limit) goto reset;
    DG8(0x1c,flags);if (flags&8u) goto reset;
    DG16(0x1ac,ratio);DG16(0x5b84,threshold);if (ratio<=threshold) goto reset;
    DG8(0x17,flags);if (flags&0x20u) goto reset;
    DG8(0x1c,flags);if (flags&4u) goto reset;
    DG8(0x1c,flags);if (flags&1u) goto reset;
    DG8(0xd7,b);DG8(0x5bad,limit);if (b<=limit) goto reset;
    DG8(0xa2,flags);if (!(flags&0x2fu)) goto reset;
    a=(uint8_t)(a+1u);DG8(0x5ba8,limit);if (a<limit) goto store;
    DG_SET(0x1e,0x40);
reset:a=0;
store:return pcm_serial_memory_write8(pcm,0x17f,a);
}
