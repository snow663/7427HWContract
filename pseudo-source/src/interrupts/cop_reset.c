#include "interrupts.h"
#include "../system/system_internal.h"
/*FFFA ->FC1F ->FC2C. Reset-entry assembly owns the transfer to7100. */
PcmStatus pcm_cop_reset(Pcm *pcm)
{
    SYS_RUN(sys_update(pcm,0,0,0x20));return PCM_RESET_BOUNDARY;
}
