#include "service_internal.h"
/*F380..F3DA. Candidates0056..005E and counters0025/002E are retained. */
PcmStatus pcm_diagnostic_clear_transmission(Pcm *pcm)
{
    static const uint16_t banks[]={0x0a,0x15};
    for (unsigned x=9;x!=0;--x) {
        for (unsigned i=0;i<2;++i) {
            uint8_t value,keep;uint16_t address=(uint16_t)(banks[i]+x);
            SVC_RUN(pcm_serial_memory_read8(pcm,address,&value));
            SVC_RUN(pcm_serial_memory_read8(pcm,(uint16_t)(0xf3dau+x),&keep));
            SVC_RUN(pcm_serial_memory_write8(pcm,address,(uint8_t)(value&keep)));
        }
    }
    SVC_RUN(svc_clear_bits(pcm,0x94,0xf0));SVC_RUN(svc_clear_bits(pcm,0x8e,0x80));
    static const uint16_t counters[]={0x1f,0x20,0x21,0x22,0x23,0x24,0x26,0x27,0x28,0x29,0x2a,0x2b,0x2c,0x2d,
        0x2f,0x30,0x31,0x182,0x183,0x184,0x185,0x32,0x33,0x34};
    for (unsigned i=0;i<sizeof(counters)/sizeof(*counters);++i) SVC_RUN(pcm_serial_memory_write8(pcm,counters[i],0));
    uint8_t sum;SVC_RUN(pcm_diagnostic_checksum(pcm,&sum));
    return pcm_serial_memory_write8(pcm,0x15,sum);
}
