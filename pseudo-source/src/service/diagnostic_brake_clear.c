#include "diagnostic_internal.h"
/* E99E..EA3F, code38: converse brake-clear speed episode and recovery. */
PcmStatus pcm_diagnostic_brake_clear(Pcm *pcm)
{
    uint8_t a,b,flags,limit;
    if (pcm->runtime.monitor_freeze) return PCM_OK;
    DG8(0x5b02,flags);if (!(flags&1u)) goto reset;
    DG8(0x9c,flags);if (!(flags&1u)) goto episode;
    DG_CLEAR(0x94,0x80);DG_SET(0x94,0x40);DG8(0x18,flags);if (!(flags&1u)) goto reset;
    DG8(0x167,a);a=(uint8_t)(a+1u);DG8(0x5b5d,limit);if (a<limit) goto store;
    DG8(0x24,b);DG8(0x5b5e,limit);if (b>=limit) goto reset;
    SYS_RUN(pcm_serial_memory_write8(pcm,0x24,(uint8_t)(b+2u)));DG_CLEAR(0x18,1);goto reset;
episode:
    DG8(0x18,flags);if (flags&1u) goto reset;
    DG8(0xd7,b);DG8(0x5b59,limit);if (b<=limit) goto lower;
    DG8(0x94,flags);if (flags&0x40u) SYS_RUN(pcm_serial_memory_write8(pcm,0x185,0));
    DG_CLEAR(0x94,0x40);DG_SET(0x94,0x80);DG8(0x185,a);a=(uint8_t)(a+1u);
    if (a!=0) { SYS_RUN(pcm_serial_memory_write8(pcm,0x185,a));a=0; }
    return pcm_serial_memory_write8(pcm,0x184,a);
lower:
    DG8(0x94,flags);if (!(flags&0x80u)) return PCM_OK;
    DG8(0x5b5a,limit);if (b<=limit) goto complete;
    DG_SET(0x94,0x40);DG8(0x184,a);a=(uint8_t)(a+1u);
    if (a!=0) SYS_RUN(pcm_serial_memory_write8(pcm,0x184,a));
    return PCM_OK;
complete:
    DG8(0x184,a);DG8(0x5b5b,limit);if (a<=limit) goto rejected;
    DG8(0x185,a);DG8(0x5b5c,limit);if (a>limit) goto qualified;
rejected:
    DG_CLEAR(0x94,0x80);DG_SET(0x94,0x40);return PCM_OK;
qualified:
    DG_CLEAR(0x94,0x80);DG_SET(0x94,0x40);DG8(0x167,a);a=(uint8_t)(a+1u);
    DG8(0x5b5d,limit);if (a<limit) goto store;
    DG_SET(0x18,1);
reset:a=0;
store:return pcm_serial_memory_write8(pcm,0x167,a);
}
