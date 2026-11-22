#include "egr_internal.h"
/* CDF7..CE0F. High command byte is always F0. The stopped-engine force path
 * writes FF even when the saved controller duty is zero. */
PcmStatus pcm_egr_output(Pcm *pcm)
{
    uint8_t flags,duty=0;SYS_RUN(pcm_read8(pcm,0x0051,&flags));
    if (!(flags&0x10u)) {
        SYS_RUN(pcm_read8(pcm,0x004f,&flags));
        if (flags&0x80u) SYS_RUN(pcm_read8(pcm,0x01af,&duty));
        else { SYS_RUN(pcm_read8(pcm,0x0071,&flags));if (flags&0x80u) duty=255; }
    }
    return pcm_write16(pcm,0x3fd8,(uint16_t)(0xf000u|duty));
}
