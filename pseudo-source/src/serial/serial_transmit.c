#include "serial_internal.h"
/*F822..F90A. Counts and address offsets retain byte wrap and ASRA behavior. */
PcmStatus pcm_serial_transmit(Pcm *pcm)
{
    uint16_t descriptor=pcm->serial.descriptor;uint8_t count=pcm->serial.count;
    if (count==1) {
        uint8_t length;SER_RUN(pcm_serial_memory_read8(pcm,(uint16_t)(descriptor+4u),&length));
        if (ser_addressed(pcm)) {
            uint8_t command=pcm->serial.last_id==0xf5 ? pcm->serial.transmission_command : pcm->serial.engine_command;
            if (command==3) { uint8_t n=(uint8_t)(pcm->serial.length-1u);length=(uint8_t)((n>>1)|(n&0x80u));++length; }
        }
        pcm->serial.length=length;return pcm_serial_send(pcm,(uint8_t)(length+0x55u));
    }
    if (count==2 && ser_addressed(pcm)) return pcm_serial_send(pcm,pcm->serial.last_id==0xf5 ? pcm->serial.transmission_command : pcm->serial.engine_command);
    uint8_t ordinal=(uint8_t)(count-2u);
    if (ordinal>=pcm->serial.length) return ordinal==pcm->serial.length ? pcm_serial_send(pcm,(uint8_t)(0u-pcm->serial.checksum)) : pcm_serial_finish(pcm);
    uint8_t value;SER_RUN(pcm_serial_next(pcm,descriptor,ordinal,&value));return pcm_serial_send(pcm,value);
}
