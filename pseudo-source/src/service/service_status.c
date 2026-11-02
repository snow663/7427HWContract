#include "service_internal.h"
/*F64E..F676. Publish0130 before beginning the independent0131 read sequence. */
PcmStatus pcm_service_status(Pcm *pcm)
{
    uint8_t a,b;SVC_RUN(pcm_serial_memory_read8(pcm,0x8c,&a));a&=0xd9;
    SVC_RUN(pcm_serial_memory_read8(pcm,0x8d,&b));a=(uint8_t)(a+(b&2u));
    SVC_RUN(pcm_serial_memory_read8(pcm,0x89,&b));a=(uint8_t)(a+(b&0x20u));
    pcm->transmission.diagnostic_status[0]=a;
    SVC_RUN(pcm_serial_memory_read8(pcm,0x93,&a));a&=0x49;
    SVC_RUN(pcm_serial_memory_read8(pcm,0x90,&b));a=(uint8_t)(a+(b&0x84u));
    SVC_RUN(pcm_serial_memory_read8(pcm,0x91,&b));a=(uint8_t)(a+((b&4u)<<2));
    SVC_RUN(pcm_serial_memory_read8(pcm,0x92,&b));
    pcm->transmission.diagnostic_status[1]=(uint8_t)(a+(b&2u));return PCM_OK;
}
