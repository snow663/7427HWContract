#include "iac.h"
#include "../system/system_internal.h"
/* 93C5..93CF: retain the coil ring; an active reset retains the whole byte. */
PcmStatus pcm_iac_step_disable(Pcm *pcm)
{
    uint8_t flags;SYS_RUN(pcm_read8(pcm,9,&flags));
    if (flags&1u) return PCM_OK;
    uint8_t control;SYS_RUN(pcm_read8(pcm,10,&control));
    return pcm_write8(pcm,10,(uint8_t)(control&0x0cu));
}
