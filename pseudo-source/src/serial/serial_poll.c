#include "serial_internal.h"
#include "control.h"
/*F5E8..F64D. Phase is an unscaled offset into overlapping schedule words. */
PcmStatus pcm_serial_poll(Pcm *pcm)
{
    if (ser_addressed(pcm)) return PCM_OK;
    uint16_t descriptor;SER_RUN(pcm_serial_memory_read16(pcm,(uint16_t)(0x518fu+(pcm->scheduler.phase&31u)),&descriptor));
    if (descriptor==0) return PCM_OK;
    uint8_t id;SER_RUN(pcm_serial_memory_read8(pcm,(uint16_t)(descriptor+2u),&id));if (id==0) return PCM_OK;
    if (pcm->serial.busy) { pcm->serial.deferred=true;return PCM_OK; }
    pcm->serial.busy=true;pcm->serial.descriptor=descriptor;
    uint8_t status;SER_RUN(pcm_read8(pcm,PCM_SCSR,&status));SER_RUN(pcm_write8(pcm,PCM_SCDR,id));pcm->serial.checksum=id;
    uint8_t length;SER_RUN(pcm_serial_memory_read8(pcm,(uint16_t)(descriptor+4u),&length));pcm->serial.length=length;
    SER_RUN(pcm_mask_irq(pcm,true));
    if (length!=0) {
        uint8_t format;SER_RUN(pcm_serial_memory_read8(pcm,(uint16_t)(descriptor+3u),&format));
        if (!(format&0xc0u)) {
            uint16_t base;SER_RUN(pcm_serial_memory_read16(pcm,(uint16_t)(descriptor+5u),&base));
            for (unsigned i=0;i<length;++i) {
                uint16_t source;uint8_t value;SER_RUN(pcm_serial_memory_read16(pcm,(uint16_t)(descriptor+9u+2u*i),&source));
                SER_RUN(pcm_serial_memory_read8(pcm,source,&value));SER_RUN(pcm_serial_memory_write8(pcm,(uint16_t)(base+i),value));
            }
        }
    }
    pcm->serial.count=1;SER_RUN(pcm_serial_driver(pcm,true));SER_RUN(pcm_mask_irq(pcm,false));return pcm_write8(pcm,PCM_SCCR2,0x88);
}
