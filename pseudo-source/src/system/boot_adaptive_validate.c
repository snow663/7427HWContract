#include "system_internal.h"
/*723F..726A. The nonzero observation concerns intermediate cumulative sums,
 *not a generic checksum-nonzero or all-cells-valid predicate. */
PcmStatus pcm_boot_adaptive_validate(Pcm *pcm)
{
    uint8_t sum=0;bool observed=false;
    for (unsigned i=0;i<52;++i) {
        uint8_t value;SYS_RUN(pcm_serial_memory_read8(pcm,(uint16_t)(0x032bu-i),&value));
        sum=(uint8_t)(sum+value);if (sum!=0) observed=true;
    }
    if (observed && sum==0) return PCM_OK;
    for (uint16_t address=0x02f8;address<=0x032b;++address)
        SYS_RUN(pcm_serial_memory_write8(pcm,address,0x80));
    return sys_update(pcm,0x3a,0,0x40);
}
