#include "serial_internal.h"
/*F8F4..F90A. Wait for the subsequent TC interrupt before releasing driver. */
PcmStatus pcm_serial_finish(Pcm *pcm)
{
    pcm->serial.companion_pending=false;pcm->serial.count=0;pcm->serial.checksum=0;pcm->serial.descriptor=0;
    uint8_t value;SER_RUN(pcm_read8(pcm,PCM_SCSR,&value));SER_RUN(pcm_read8(pcm,PCM_SCDR,&value));
    return pcm_write8(pcm,PCM_SCCR2,0x40);
}
