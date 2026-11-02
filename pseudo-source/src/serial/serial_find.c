#include "serial_internal.h"
/*F927..F939. Mutable descriptor graphs have a full16-bit-domain traversal bound;
 * exceeding it is a configuration error, not an invented protocol whitelist. */
PcmStatus pcm_serial_find(Pcm *pcm,uint8_t id,uint16_t *descriptor)
{
    if (descriptor==NULL) return PCM_BAD_CONFIGURATION;
    uint16_t next=pcm->io.diagnostic_warm ? 0xfbd7 : 0x51bf;
    for (uint32_t hops=0;hops<65536u;++hops) {
        uint8_t candidate;SER_RUN(pcm_serial_memory_read8(pcm,(uint16_t)(next+2u),&candidate));
        if (id==candidate) { *descriptor=next;return PCM_OK; }
        SER_RUN(pcm_serial_memory_read16(pcm,next,&next));
        if (next==0) { *descriptor=0;return PCM_OK; }
    }
    return PCM_BAD_CONFIGURATION;
}
