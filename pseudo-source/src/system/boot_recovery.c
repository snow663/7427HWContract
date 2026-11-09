#include "system_internal.h"
/*726B..7392, ending at the actual7393 controller entry. CLRB726E supplies
 *the zero used by the final STAB stores; no intervening callee changes B. */
PcmStatus pcm_boot_recovery(Pcm *pcm)
{
    uint8_t initial;SYS_RUN(pcm_read8(pcm,0x4132,&initial));
    SYS_RUN(pcm_write16(pcm,0x01f6,(uint16_t)((uint16_t)initial*256u)));
    static const uint16_t thresholds[]={0x5b1e,0x5b21,0x5b42,0x5b52,0x5b58,0x5b5e,0x5b62,
        0x5b75,0x5b76,0x5b7a,0x5b8c,0x5b90,0x5ba3,0x5ba5,0x5ba7,0x5ba9,0x5bab,0x5bc0,0x5bca};
    for (unsigned i=0;i<sizeof(thresholds)/sizeof(*thresholds);++i) {
        uint16_t address=(uint16_t)(0x1fu+i);uint8_t count;
        SYS_RUN(pcm_serial_memory_read8(pcm,address,&count));
        if (count!=0) {
            uint8_t threshold;SYS_RUN(pcm_read8(pcm,thresholds[i],&threshold));
            if (count<threshold) SYS_RUN(pcm_serial_memory_write8(pcm,address,(uint8_t)(count-1u)));
        }
    }
    uint8_t flags;SYS_RUN(pcm_serial_memory_read8(pcm,0x1e,&flags));
    if (flags&4u) {
        uint8_t count,threshold;SYS_RUN(pcm_serial_memory_read8(pcm,0x31,&count));
        SYS_RUN(pcm_read8(pcm,0x5bca,&threshold));
        if (count<threshold) {
            SYS_RUN(pcm_serial_memory_write8(pcm,0x31,(uint8_t)(count+2u)));
            SYS_RUN(sys_update(pcm,0x1e,4,0));
        }
    }
    SYS_RUN(sys_update(pcm,0x19,4,0));SYS_RUN(sys_update(pcm,0x19,2,0));
    uint8_t mode;SYS_RUN(pcm_read8(pcm,0x400f,&mode));
    if (mode&0x80u) SYS_RUN(sys_update(pcm,0x17,0x20,0));
    for (unsigned i=0;i<3;++i) {
        uint8_t count,threshold;uint16_t address=(uint16_t)(0x32u+i);
        SYS_RUN(pcm_serial_memory_read8(pcm,address,&count));
        SYS_RUN(pcm_read8(pcm,(uint16_t)(0x5bc7u+i),&threshold));
        if (count>=threshold) SYS_RUN(pcm_serial_memory_write8(pcm,address,0));
    }
    return PCM_OK;
}
