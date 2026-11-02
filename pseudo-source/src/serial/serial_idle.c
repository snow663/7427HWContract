#include "serial_internal.h"
/*F781..F7E9. Expiry clears selected flags/commands and preserves other payload. */
PcmStatus pcm_serial_idle(Pcm *pcm)
{
    SER_RUN(pcm_mask_irq(pcm,true));
    if (ser_addressed(pcm)) {
        uint8_t age=(uint8_t)(pcm->serial.receive_age+1u);
        if (age!=0) pcm->serial.receive_age=age;
        if (age==0 || age>=200) {
            pcm->serial.transmission_command=0;pcm->serial.engine_command=0;pcm->serial.sessions&=0xfcu;
            pcm->serial.clear_edges&=0x2fu;pcm->serial.busy=false;pcm->serial.clear_engine=false;pcm->serial.clear_transmission=false;
            SER_RUN(pcm_serial_driver(pcm,false));SER_RUN(pcm_write8(pcm,PCM_SCCR2,0x26));
            pcm->serial.descriptor=0;pcm->serial.count=0;pcm->serial.checksum=0;
        }
    }
    SER_RUN(pcm_mask_irq(pcm,false));
    if (pcm->runtime.engine_service || pcm->runtime.transmission_service) {
        uint16_t age=(uint16_t)(pcm->serial.service_age+1u);pcm->serial.service_age=age;
        uint16_t threshold;SER_RUN(pcm_serial_memory_read16(pcm,0x51bb,&threshold));
        if (age>=threshold) pcm->serial.service_expiry=1;
    } else {
        uint16_t expiry=pcm->serial.service_expiry;
        if (expiry==0) return PCM_OK;
        expiry=(uint16_t)(expiry+1u);pcm->serial.service_expiry=expiry;
        uint16_t threshold;SER_RUN(pcm_serial_memory_read16(pcm,0x51bd,&threshold));
        if (expiry>=threshold) { pcm->serial.service_expiry=0;pcm->serial.service_age=0; }
    }
    return PCM_OK;
}
