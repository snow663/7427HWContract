#include "serial_internal.h"
/*F96B..F9B5. Ordinary command/page selection precedes the shared-buffer store. */
PcmStatus pcm_serial_payload(Pcm *pcm,uint16_t descriptor,uint8_t ordinal,uint8_t value)
{
    if (ser_addressed(pcm)) {
        if (ordinal==0) {
            if (value>10) return pcm_serial_abort(pcm);
            SER_RUN(pcm_serial_memory_read16(pcm,(uint16_t)(descriptor+9u+2u*value),&descriptor));
            if (descriptor==0) return pcm_serial_abort(pcm);
            pcm->serial.descriptor=descriptor;
        } else if (pcm->serial.receive[0]==1 && ordinal==1) {
            if (value>=3) value=0;
            SER_RUN(pcm_serial_memory_read16(pcm,(uint16_t)(descriptor-6u+2u*value),&descriptor));
            pcm->serial.descriptor=descriptor;
        }
    }
    uint16_t destination;SER_RUN(pcm_serial_memory_read16(pcm,(uint16_t)(descriptor+7u),&destination));
    SER_RUN(pcm_serial_memory_write8(pcm,(uint16_t)(destination+ordinal),value));
    ++pcm->serial.count;return PCM_OK;
}
