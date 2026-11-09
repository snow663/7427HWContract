#include "system_internal.h"
/* FAAD..FAC6. X is captured once; source bytes and the complemented final ID
 * are live reads. Forward overlap and address wrap are intentional. */
PcmStatus pcm_factory_upload(Pcm *pcm)
{
    SYS_RUN(sys_update(pcm,1,1,0));
    uint16_t destination;SYS_RUN(pcm_serial_memory_read16(pcm,0x038e,&destination));
    for (unsigned i=0;i<32;++i) {
        uint8_t value;SYS_RUN(pcm_serial_memory_read8(pcm,(uint16_t)(0x0390u+i),&value));
        SYS_RUN(pcm_serial_memory_write8(pcm,(uint16_t)(destination+i),value));
    }
    uint8_t id;SYS_RUN(pcm_serial_memory_read8(pcm,0x0364,&id));
    return pcm_serial_memory_write8(pcm,0x0364,(uint8_t)~id);
}
