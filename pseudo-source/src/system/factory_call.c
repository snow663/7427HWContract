#include "system_internal.h"
/* FA9F..FAA6. There is no resident destination whitelist or alignment gate. */
PcmStatus pcm_factory_call(Pcm *pcm)
{
    SYS_RUN(sys_update(pcm,1,0,1));
    uint16_t address;SYS_RUN(pcm_serial_memory_read16(pcm,0x038e,&address));
    if (pcm->platform==NULL || pcm->platform->call_address==NULL) return PCM_NO_HARDWARE;
    return pcm->platform->call_address(pcm->platform->context,address);
}
