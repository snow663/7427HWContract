#include "interrupts.h"
#include "../system/system_internal.h"
/*FFFC ->FC24. The resident body halts at FC27 rather than jumping to7100. */
PcmStatus pcm_clock_failure(Pcm *pcm)
{
    SYS_RUN(sys_update(pcm,0,0,0x40));return PCM_HALT_BOUNDARY;
}
