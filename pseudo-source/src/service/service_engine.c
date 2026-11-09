#include "service_internal.h"
/*F715..F738. BLM rearm occurs only in a qualified engine04 branch. */
PcmStatus pcm_service_engine(Pcm *pcm)
{
    if ((pcm->serial.sessions&1u) && pcm->serial.engine_command==4) {
        pcm->runtime.engine_service=true;
        uint8_t flags;SVC_RUN(pcm_serial_memory_read8(pcm,0x391,&flags));
        if (flags&0x10u) {
            if (!(pcm->serial.clear_edges&0x10u)) {
                SVC_RUN(pcm_blm_reset(pcm));pcm->serial.clear_edges|=0x10;
            }
        } else pcm->serial.clear_edges&=0xefu;
    }
    return PCM_OK;
}
