#include "service_internal.h"
/*F333..F376. Three keep-mask reads per index; no SEI/CLI is inserted. */
PcmStatus pcm_diagnostic_clear_engine(Pcm *pcm)
{
    static const uint16_t banks[]={0x0a,0x15,0x55};
    for (unsigned x=9;x!=0;--x) {
        for (unsigned i=0;i<3;++i) {
            uint8_t value,keep;uint16_t address=(uint16_t)(banks[i]+x);
            SVC_RUN(pcm_serial_memory_read8(pcm,address,&value));
            SVC_RUN(pcm_serial_memory_read8(pcm,(uint16_t)(0xf376u+x),&keep));
            SVC_RUN(pcm_serial_memory_write8(pcm,address,(uint8_t)(value&keep)));
        }
    }
    SVC_RUN(svc_clear_bits(pcm,4,0x80));SVC_RUN(svc_clear_bits(pcm,0x44,0x80));
    SVC_RUN(svc_clear_bits(pcm,0x72,1));SVC_RUN(svc_clear_bits(pcm,0x6f,0x10));
    SVC_RUN(svc_clear_bits(pcm,0x70,1));
    static const uint16_t counters[]={0x1f,0x20,0x817,0x21c,0x81c};
    for (unsigned i=0;i<sizeof(counters)/sizeof(*counters);++i) SVC_RUN(pcm_serial_memory_write8(pcm,counters[i],0));
    uint8_t sum;SVC_RUN(pcm_diagnostic_checksum(pcm,&sum));
    return pcm_serial_memory_write8(pcm,0x15,sum);
}
