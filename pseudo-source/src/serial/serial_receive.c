#include "serial_internal.h"
/*F90B..FA5A. Read status/data before clearing age; failed frames retain stores. */
PcmStatus pcm_serial_receive(Pcm *pcm)
{
    uint8_t status,value;SER_RUN(pcm_read8(pcm,PCM_SCSR,&status));SER_RUN(pcm_read8(pcm,PCM_SCDR,&value));
    uint16_t descriptor=pcm->serial.descriptor;pcm->serial.receive_age=0;
    if (status&0x0eu) return pcm_serial_abort(pcm);
    pcm->serial.checksum=(uint8_t)(pcm->serial.checksum+value);
    uint8_t count=pcm->serial.count;
    if (count==0) {
        SER_RUN(pcm_serial_find(pcm,value,&descriptor));
        if (descriptor==0) return pcm_serial_abort(pcm);
        if (value==0xf4) pcm->serial.sessions|=1u;
        else if (value==0xf5) pcm->serial.sessions|=2u;
        pcm->serial.descriptor=descriptor;SER_RUN(pcm_write8(pcm,PCM_SCCR2,0x24));
        ++pcm->serial.count;return PCM_OK;
    }
    if (count==1) {
        if (value<0x55 || (uint8_t)(value-0x55u)>34) return pcm_serial_abort(pcm);
        pcm->serial.length=(uint8_t)(value-0x55u);++pcm->serial.count;return PCM_OK;
    }
    uint8_t ordinal=(uint8_t)(count-2u);
    if (ordinal<pcm->serial.length) return pcm_serial_payload(pcm,descriptor,ordinal,value);
    return pcm->serial.checksum!=0 ? pcm_serial_abort(pcm) : pcm_serial_accept(pcm,descriptor);
}
