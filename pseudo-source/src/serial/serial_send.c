#include "serial_internal.h"
/*F8E6..F8F3. Sample checksum/count after the hardware write callback. */
PcmStatus pcm_serial_send(Pcm *pcm,uint8_t value)
{
    SER_RUN(pcm_write8(pcm,PCM_SCDR,value));
    pcm->serial.checksum=(uint8_t)(value+pcm->serial.checksum);++pcm->serial.count;
    return PCM_OK;
}
