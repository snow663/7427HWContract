#include "serial_internal.h"
/*FA28..FA4C. Descriptor is a captured X value; checksum/count commit after ID. */
PcmStatus pcm_serial_start(Pcm *pcm,uint16_t descriptor)
{
    pcm->serial.descriptor=descriptor;
    uint8_t status,id;SER_RUN(pcm_read8(pcm,PCM_SCSR,&status));
    SER_RUN(pcm_serial_memory_read8(pcm,(uint16_t)(descriptor+2u),&id));
    SER_RUN(pcm_write8(pcm,PCM_SCDR,id));
    pcm->serial.checksum=id;pcm->serial.count=1;
    SER_RUN(pcm_serial_driver(pcm,true));return pcm_write8(pcm,PCM_SCCR2,0x88);
}
