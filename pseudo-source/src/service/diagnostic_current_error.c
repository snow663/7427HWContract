#include "diagnostic_internal.h"
/* EC2D..EC78, code73: literal eight-bit negation (including80), inhibit
 * timer0178 and a one-time good-observation recovery allowance. */
PcmStatus pcm_diagnostic_current_error(Pcm *pcm)
{
    uint8_t a,b,flags,limit;
    if (pcm->runtime.monitor_freeze) return PCM_OK;
    DG8(0x5b06,flags);if (!(flags&2u)) goto reset;
    DG8(0x176,a);DG8(0x8e,flags);if (flags&0x80u) goto test;
    DG8(0x14f,b);if (b&0x80u) b=(uint8_t)(0u-b);
    DG8(0x5b8e,limit);if (b>limit) goto test;
    DG8(0x95,flags);if (flags&0x20u) goto reset;
    DG_SET(0x95,0x20);DG8(0x1c,flags);if (!(flags&2u)) goto reset;
    DG8(0x2a,b);DG8(0x5b90,limit);if (b>=limit) goto reset;
    SYS_RUN(pcm_serial_memory_write8(pcm,0x2a,(uint8_t)(b+2u)));DG_CLEAR(0x1c,2);goto reset;
test:
    DG8(0x1d,flags);if (flags&0x80u) goto reset;
    DG8(0x178,flags);if (flags!=0) goto reset;
    a=(uint8_t)(a+1u);DG8(0x5b8f,limit);if (a<limit) goto store;
    DG_SET(0x1c,2);
reset:a=0;
store:return pcm_serial_memory_write8(pcm,0x176,a);
}
