#include "interrupts.h"
#include "../system/system_internal.h"
/*FFFE ->FC29 ->FC2C. Cause bits can later be cleared by retained validation. */
PcmStatus pcm_external_reset(Pcm *pcm)
{
    SYS_RUN(sys_update(pcm,0,0,0x80));return PCM_RESET_BOUNDARY;
}
