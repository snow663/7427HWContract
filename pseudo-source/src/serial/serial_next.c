#include "serial_internal.h"
/*F86E..F8DE. Caller has tested payload/checksum priority before companion. */
PcmStatus pcm_serial_next(Pcm *pcm,uint16_t descriptor,uint8_t ordinal,uint8_t *out)
{
    if (out==NULL) return PCM_BAD_CONFIGURATION;
    if (pcm->serial.companion_pending) { pcm->serial.companion_pending=false;*out=pcm->serial.companion;return PCM_OK; }
    uint8_t format;SER_RUN(pcm_serial_memory_read8(pcm,(uint16_t)(descriptor+3u),&format));
    uint16_t address;
    if (format&0x80u) {
        if (ser_addressed(pcm)) --ordinal;
        uint8_t offset=(uint8_t)(2u*ordinal);
        SER_RUN(pcm_serial_memory_read16(pcm,(uint16_t)(descriptor+9u+offset),&address));
    } else {
        /*F876 performs a fresh second descriptor read after the failed80 gate. */
        SER_RUN(pcm_serial_memory_read8(pcm,(uint16_t)(descriptor+3u),&format));
        if (format&0x40u) {
            --ordinal;uint16_t base;SER_RUN(pcm_serial_memory_read16(pcm,(uint16_t)(descriptor+5u),&base));
            uint8_t command=pcm->serial.last_id==0xf4 ? pcm->serial.engine_command : pcm->serial.last_id==0xf5 ? pcm->serial.transmission_command : 0;
            if (command==2) {
                SER_RUN(pcm_serial_memory_read16(pcm,(uint16_t)(base+1u),&address));address=(uint16_t)(address+ordinal);
            } else {
                uint8_t offset=(uint8_t)(2u*ordinal+1u);if (command==4) offset=(uint8_t)(offset+10u);
                SER_RUN(pcm_serial_memory_read16(pcm,(uint16_t)(base+offset),&address));
            }
        } else {
            SER_RUN(pcm_serial_memory_read16(pcm,(uint16_t)(descriptor+5u),&address));
            return pcm_serial_memory_read8(pcm,(uint16_t)(address+ordinal),out);
        }
    }
    if (address>=0x1000 && address<=0x3fff) {
        if (!pcm->io.diagnostic_warm) address &= 0xcfffu;
        uint16_t word;SER_RUN(pcm_serial_memory_read16(pcm,address,&word));
        pcm->serial.companion=(uint8_t)word;pcm->serial.companion_pending=true;*out=(uint8_t)(word>>8);return PCM_OK;
    }
    return pcm_serial_memory_read8(pcm,address,out);
}
