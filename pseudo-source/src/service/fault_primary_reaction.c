#include "control.h"
#include "../system/system_internal.h"
/*E62D..E653. Alternate reaction polarity uses Aj, unlike E6BC's ~Aj.
 * Scan bank9 down to1 and stop on the first nonzero four-way intersection. */
PcmStatus pcm_fault_primary_reaction(Pcm *pcm)
{
    uint8_t alternate,reaction,fault,mask;bool found=false;
    for (unsigned bank=9;bank!=0;--bank) {
        SYS_RUN(pcm_read8(pcm,(uint16_t)(0x5b33u+bank),&alternate));
        SYS_RUN(pcm_read8(pcm,(uint16_t)(0x5b2au+bank),&reaction));
        SYS_RUN(pcm_read8(pcm,(uint16_t)(0x0015u+bank),&fault));
        SYS_RUN(pcm_read8(pcm,(uint16_t)(0xe716u+bank),&mask));
        if (alternate&reaction&fault&mask) { found=true;break; }
    }
    return sys_update(pcm,0x0098,found?0:8,found?8:0);
}
