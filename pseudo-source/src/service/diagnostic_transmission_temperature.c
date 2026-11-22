#include "diagnostic_internal.h"
/* ECFF..ED3E, code79: asymmetric temperature hysteresis and wrapped
 * sixteen-bit qualification timer. Fault entry is inhibited by001B.6. */
PcmStatus pcm_diagnostic_transmission_temperature(Pcm *pcm)
{
    uint8_t sample,flags,limit;uint16_t timer,threshold;
    if (pcm->runtime.monitor_freeze) return PCM_OK;
    DG8(0x5b07,flags);if (!(flags&8u)) goto reset;
    DG16(0x17a,timer);DG8(0xb5,sample);DG8(0x1d,flags);if (!(flags&8u)) goto entering;
    DG8(0x5b9e,limit);if (sample>=limit) goto reset;
    timer=(uint16_t)(timer+1u);DG16(0x5ba0,threshold);if (timer<threshold) goto store;
    DG_CLEAR(0x1d,8);goto reset;
entering:
    DG8(0x5b9f,limit);if (sample<limit) goto reset;
    DG8(0x1b,flags);if (flags&0x40u) goto reset;
    timer=(uint16_t)(timer+1u);DG16(0x5ba0,threshold);if (timer<threshold) goto store;
    DG_SET(0x1d,8);
reset:timer=0;
store:return pcm_write16(pcm,0x17a,timer);
}
