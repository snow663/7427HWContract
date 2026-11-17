#include "system_internal.h"
#include "service.h"
#include "fuel.h"
/*720C..723E. Failure clears the three exact ranges, seeds TPS zero and all
 *21 BLM cells, then sets0046.6. Acceptance retains those areas. */
PcmStatus pcm_boot_retained_validate(Pcm *pcm)
{
    uint8_t actual,expected;SYS_RUN(pcm_diagnostic_checksum(pcm,&actual));
    SYS_RUN(pcm_serial_memory_read8(pcm,0x15,&expected));
    if (actual!=expected) {
        SYS_RUN(pcm_ram_clear(pcm,0,0x0b));
        SYS_RUN(pcm_ram_clear(pcm,0x0b,0x2b));
        SYS_RUN(pcm_ram_clear(pcm,0x029d,0x00b1));
        uint8_t minimum;SYS_RUN(pcm_read8(pcm,0x5b24,&minimum));
        SYS_RUN(pcm_write16(pcm,0x02f6,(uint16_t)((uint16_t)minimum*256u+128u)));
        SYS_RUN(pcm_blm_reset(pcm));
        SYS_RUN(sys_update(pcm,0x46,0,0x40));
    }
    return sys_update(pcm,0x86,0,8);
}
