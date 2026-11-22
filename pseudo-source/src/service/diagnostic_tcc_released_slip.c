#include "diagnostic_internal.h"
/* EEBC..EF2A, code69: signed open slip window while the TCC is released. */
PcmStatus pcm_diagnostic_tcc_released_slip(Pcm *pcm)
{
    uint8_t a,b,flags,limit;uint16_t sample,threshold;
    if (pcm->runtime.monitor_freeze) return PCM_OK;
    DG8(0x5b06,flags);if (!(flags&0x10u)) goto reset;
    DG8(0x173,a);DG8(0x95,flags);if (flags&8u) goto test;
    DG_SET(0x95,8);DG8(0x1c,flags);if (!(flags&0x10u)) goto reset;
    DG_CLEAR(0x1c,0x10);goto reset;
test:
    DG8(0x1c,flags);if (flags&0x10u) goto reset;
    DG16(0xeb,sample);DG16(0x5b7d,threshold);if (dg_signed(sample)<=dg_signed(threshold)) goto reset;
    DG16(0x5b7b,threshold);if (dg_signed(sample)>=dg_signed(threshold)) goto reset;
    DG8(0xb2,b);DG8(0x5b80,limit);if (b<=limit) goto reset;
    DG8(0x16,flags);if (flags&1u) goto reset;
    DG8(0x17,flags);if (flags&0x80u) goto reset;
    DG8(0x89,flags);if (flags&0x20u) goto reset;
    DG8(0xd9,b);if (b==0 || b==3) goto reset;
    DG8(0x1c,flags);if (flags&8u) goto reset;
    DG16(0x1ac,sample);DG16(0x5b84,threshold);if (sample<=threshold) goto reset;
    DG8(0x1c,flags);if (flags&1u) goto reset;
    DG8(0x17,flags);if (flags&2u) goto reset;
    DG8(0xa2,flags);if (!(flags&0x0cu)) goto reset;
    a=(uint8_t)(a+1u);DG8(0x5b7f,limit);if (a<limit) goto store;
    DG_SET(0x1c,0x10);
reset:a=0;
store:return pcm_serial_memory_write8(pcm,0x173,a);
}
