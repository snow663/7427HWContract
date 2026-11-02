#include "serial_internal.h"
/*F9BE..FA27. Retained command bytes remain meaningful for a valid N=0 frame. */
PcmStatus pcm_serial_accept(Pcm *pcm,uint16_t descriptor)
{
    uint8_t id;SER_RUN(pcm_serial_memory_read8(pcm,(uint16_t)(descriptor+2u),&id));
    pcm->serial.last_id=id;uint8_t count=pcm->serial.length;
    uint16_t destination=0x38e;
    if (!pcm->io.diagnostic_warm) {
        if (id==0xf5) destination=0x399;
        pcm->serial.clear_engine=false;pcm->serial.clear_transmission=false;
        uint8_t command=pcm->serial.receive[0];SER_RUN(pcm_serial_memory_write8(pcm,destination,command));
        if (command==0) { pcm->serial.sessions &= destination==0x399 ? 0xfdu : 0xfeu;goto reply; }
        if (command==10) {
            if (pcm->serial.last_id==0xf5) pcm->serial.clear_transmission=true;
            else pcm->serial.clear_engine=true;
            goto reply;
        }
        if (command!=4) goto reply;
        if (count>11) count=11;
    }
    for (uint8_t i=0;i<count;++i) {
        uint8_t value;SER_RUN(pcm_serial_memory_read8(pcm,(uint16_t)(0x36cu+i),&value));
        SER_RUN(pcm_serial_memory_write8(pcm,(uint16_t)(destination+i),value));
    }
reply:
    descriptor=pcm->serial.descriptor;
    uint8_t length;SER_RUN(pcm_serial_memory_read8(pcm,(uint16_t)(descriptor+4u),&length));
    return (length&0x80u) ? pcm_serial_abort(pcm) : pcm_serial_start(pcm,descriptor);
}
