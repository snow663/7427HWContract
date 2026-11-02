#include "serial_internal.h"
/* Preserve word callback width for foreign/device addresses. Fully owned serial
 * words are read from their canonical fields, without a stale mirror buffer. */
PcmStatus pcm_serial_memory_read16(Pcm *pcm,uint16_t address,uint16_t *out)
{
    if (out==NULL) return PCM_BAD_CONFIGURATION;
    if (address==0x362) { *out=pcm->serial.descriptor;return PCM_OK; }
    if (address==0x368) { *out=pcm->serial.service_age;return PCM_OK; }
    if (address==0x36a) { *out=pcm->serial.service_expiry;return PCM_OK; }
    uint8_t high,low;
    if (ser_get(pcm,address,&high) && ser_get(pcm,(uint16_t)(address+1u),&low)) {
        *out=(uint16_t)((uint16_t)high*256u+low);return PCM_OK;
    }
    return pcm_read16(pcm,address,out);
}
