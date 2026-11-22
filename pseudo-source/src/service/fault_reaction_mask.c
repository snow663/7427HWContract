#include "control.h"
#include "../system/system_internal.h"
/*E6BC..E6E3. X names the byte before the nine masks; ABX wraps at16 bits.
 * Return A only after the full scan or first nonzero intersection completes. */
PcmStatus pcm_fault_reaction_mask(Pcm *pcm,uint16_t mask_base,uint8_t *value)
{
    if (value==NULL) return PCM_BAD_CONFIGURATION;
    uint8_t alternate,reaction,fault,mask,result=0;
    for (unsigned bank=9;bank!=0;--bank) {
        SYS_RUN(pcm_read8(pcm,(uint16_t)(0x5b33u+bank),&alternate));
        SYS_RUN(pcm_read8(pcm,(uint16_t)(0x5b2au+bank),&reaction));
        SYS_RUN(pcm_read8(pcm,(uint16_t)(0x0015u+bank),&fault));
        SYS_RUN(pcm_read8(pcm,(uint16_t)(mask_base+bank),&mask));
        result=(uint8_t)((uint8_t)~alternate&reaction&fault&mask);if (result!=0) break;
    }
    *value=result;return PCM_OK;
}
