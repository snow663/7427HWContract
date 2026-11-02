#include "service_internal.h"
/*F326..F332. Read age0014 followed by nine retained bytes in descending order. */
PcmStatus pcm_diagnostic_checksum(Pcm *pcm,uint8_t *out)
{
    if (out==NULL) return PCM_BAD_CONFIGURATION;
    uint8_t sum=0;
    for (unsigned i=0;i<10;++i) {
        uint8_t value;SVC_RUN(pcm_serial_memory_read8(pcm,(uint16_t)(0x14u-i),&value));
        sum=(uint8_t)(sum-value);
    }
    *out=sum;return PCM_OK;
}
