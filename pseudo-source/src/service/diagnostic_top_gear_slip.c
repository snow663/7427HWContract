#include "diagnostic_internal.h"
/* EE61..EEBB, code68: unsigned absolute slip and third-gear qualification. */
PcmStatus pcm_diagnostic_top_gear_slip(Pcm *pcm)
{
    uint8_t a,b,flags,limit;uint16_t sample,threshold;
    if (pcm->runtime.monitor_freeze) return PCM_OK;
    DG8(0x5b06,flags);if (!(flags&0x20u)) goto reset;
    DG8(0x172,a);DG16(0xed,sample);DG16(0x5b77,threshold);if (sample>threshold) goto test;
    DG8(0x95,flags);if (flags&4u) goto reset;
    DG_SET(0x95,4);DG8(0x1c,flags);if (!(flags&0x20u)) goto reset;
    DG8(0x28,b);DG8(0x5b7a,limit);if (b>=limit) goto reset;
    SYS_RUN(pcm_serial_memory_write8(pcm,0x28,(uint8_t)(b+2u)));DG_CLEAR(0x1c,0x20);goto reset;
test:
    DG8(0x1c,flags);if (flags&0x20u) goto reset;
    DG8(0xd9,b);if (b!=3) goto reset;
    DG8(0x89,flags);if (!(flags&0x20u)) goto reset;
    DG8(0x1c,flags);if (flags&8u) goto reset;
    DG8(0x1c,flags);if (flags&1u) goto reset;
    DG8(0x17,flags);if (flags&2u) goto reset;
    DG8(0xa2,flags);if (!(flags&0x0fu)) goto reset;
    a=(uint8_t)(a+1u);DG8(0x5b79,limit);if (a<limit) goto store;
    DG_SET(0x1c,0x20);
reset:a=0;
store:return pcm_serial_memory_write8(pcm,0x172,a);
}
