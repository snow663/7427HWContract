#include "service_internal.h"
/*F677..F714. Session/selector/cooldown admission and asymmetric cleanup. */
PcmStatus pcm_service_transmission(Pcm *pcm)
{
    if ((pcm->serial.sessions&2u) && pcm->serial.transmission_command==4 && pcm->serial.service_expiry==0) {
        pcm->runtime.transmission_service=true;
        uint8_t a=0;
        if (pcm->transmission.current_service_enable&0x18u) {
            if ((pcm->transmission.current_service_enable&8u) && (pcm->transmission.current_service_value&8u)) a|=1;
            if ((pcm->transmission.current_service_enable&0x10u) && (pcm->transmission.current_service_value&0x10u)) a|=2;
            unsigned gear;
            for (gear=0;gear<3;++gear) {
                uint8_t pattern;SVC_RUN(pcm_serial_memory_read8(pcm,(uint16_t)(0xb319u+gear),&pattern));
                if (a==pattern) break;
            }
            pcm->transmission.service_gear=(uint8_t)(gear+1u);
        }
        uint8_t selector;SVC_RUN(pcm_serial_memory_read8(pcm,0x39e,&selector));
        if (selector&0x80u) {
            SVC_RUN(pcm_serial_memory_read8(pcm,0x39f,&a));pcm->transmission.service_tcc=a;
        }
        if (pcm->runtime.transmission_service) {
            a=(uint8_t)(pcm->transmission.adaptive_flags&0xbfu);
            SVC_RUN(pcm_serial_memory_read8(pcm,0x3a0,&selector));if (selector&0x40u) a|=0x40;
            pcm->transmission.adaptive_flags=a;
            a=(uint8_t)(pcm->transmission.adaptive_flags&0x7fu);
            SVC_RUN(pcm_serial_memory_read8(pcm,0x3a0,&selector));if (selector&0x80u) a|=0x80;
        }
        pcm->transmission.adaptive_flags=a;
        SVC_RUN(pcm_serial_memory_read8(pcm,0x3a1,&a));pcm->transmission.service_pressure=a;
    }
    if (pcm->runtime.transmission_service && (!(pcm->serial.sessions&2u) || pcm->serial.service_expiry!=0)) {
        pcm->serial.transmission_command=0;pcm->transmission.service_tcc=0;pcm->transmission.service_gear=0;
        pcm->transmission.service_pressure=0;pcm->transmission.service_state=0;pcm->runtime.transmission_service=false;
    }
    return PCM_OK;
}
