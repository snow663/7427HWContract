#include "interrupts.h"
#include "../system/system_internal.h"
/*FFF6 ->FC04. Preserve existing causes, then stop before FC07's self-loop. */
PcmStatus pcm_swi_irq(Pcm *pcm)
{
    SYS_RUN(sys_update(pcm,0,0,8));return PCM_HALT_BOUNDARY;
}
