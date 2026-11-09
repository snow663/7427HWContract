#include "system_internal.h"
#include "service.h"
/*71C3..720B. Failure removes3FFC.3, records code51 and compares the captured
 *082F sample forever when>=64. That nonreturning point is an explicit boundary. */
PcmStatus pcm_boot_rom_validate(Pcm *pcm)
{
    SYS_RUN(sys_update(pcm,5,0x10,0));
    uint8_t config;SYS_RUN(pcm_read8(pcm,0x303f,&config));
    if (config!=0x0b) SYS_RUN(sys_update(pcm,0x3a,0,4));
    else {
        uint16_t actual,expected;uint8_t id;
        SYS_RUN(pcm_rom_checksum(pcm,&actual));
        SYS_RUN(pcm_read8(pcm,0x4008,&id));
        SYS_RUN(pcm_read16(pcm,0x4006,&expected));
        if ((actual==expected && id==0x31) || id==0xaa) return PCM_OK;
        SYS_RUN(sys_update(pcm,0x3a,0,2));
    }
    SYS_RUN(sys_update(pcm,5,0,0x10));
    uint16_t control;SYS_RUN(pcm_read16(pcm,PCM_BOARD_CONTROL,&control));
    SYS_RUN(pcm_delay_cycles(pcm,11));
    SYS_RUN(pcm_write16(pcm,PCM_BOARD_CONTROL,(uint16_t)(control&0xfff7u)));
    SYS_RUN(sys_update(pcm,0x1a,0,0x20));
    SYS_RUN(sys_update(pcm,0x0f,0,0x20));
    uint8_t sum;SYS_RUN(pcm_diagnostic_checksum(pcm,&sum));
    SYS_RUN(pcm_serial_memory_write8(pcm,0x15,sum));
    uint8_t sample;SYS_RUN(pcm_serial_memory_read8(pcm,0x82f,&sample));
    return sample>=0x64?PCM_BOOT_WAIT_BOUNDARY:PCM_OK;
}
