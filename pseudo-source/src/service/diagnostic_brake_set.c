#include "diagnostic_internal.h"
/* E905..E99D, code37: brake-set speed episode. Age counters suppress a
 * wrapped-zero write; the fault timer itself wraps and several exits retain it. */
PcmStatus pcm_diagnostic_brake_set(Pcm *pcm)
{
    uint8_t a,b,flags,limit;
    if (pcm->runtime.monitor_freeze) return PCM_OK;
    DG8(0x5b02,flags);if (!(flags&2u)) goto reset;
    DG8(0x9c,flags);if (flags&1u) goto episode;
    DG_CLEAR(0x94,0x30);DG8(0x18,flags);if (!(flags&2u)) goto reset;
    DG8(0x166,a);a=(uint8_t)(a+1u);DG8(0x5b57,limit);if (a<limit) goto store;
    DG8(0x23,b);DG8(0x5b58,limit);if (b>=limit) goto reset;
    SYS_RUN(pcm_serial_memory_write8(pcm,0x23,(uint8_t)(b+2u)));DG_CLEAR(0x18,2);goto reset;
episode:
    DG8(0x18,flags);if (flags&2u) goto reset;
    DG8(0xd7,b);DG8(0x5b53,limit);if (b>limit) goto above;
    DG_SET(0x94,0x10);DG_CLEAR(0x94,0x20);
    return pcm_serial_memory_write8(pcm,0x182,0);
above:
    DG8(0x94,flags);if (!(flags&0x10u)) return PCM_OK;
    DG8(0x5b54,limit);if (b>=limit) goto high;
    DG8(0x94,flags);if (flags&0x20u) goto rejected;
    DG8(0x182,a);a=(uint8_t)(a+1u);
    if (a!=0) { SYS_RUN(pcm_serial_memory_write8(pcm,0x182,a));a=0; }
    return pcm_serial_memory_write8(pcm,0x183,a);
high:
    DG_SET(0x94,0x20);DG8(0x183,a);a=(uint8_t)(a+1u);
    if (a!=0) SYS_RUN(pcm_serial_memory_write8(pcm,0x183,a));
    DG8(0x182,a);DG8(0x5b55,limit);if (a>limit) goto qualified;
rejected:
    DG_CLEAR(0x94,0x30);return PCM_OK;
qualified:
    DG8(0x183,a);DG8(0x5b56,limit);if (a<=limit) return PCM_OK;
    DG_CLEAR(0x94,0x30);DG8(0x166,a);a=(uint8_t)(a+1u);
    DG8(0x5b57,limit);if (a<limit) goto store;
    DG_SET(0x18,2);
reset:a=0;
store:return pcm_serial_memory_write8(pcm,0x166,a);
}
