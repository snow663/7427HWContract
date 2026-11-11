#include "interrupts.h"
#include "../system/system_internal.h"
/*FFF8 ->FC1A; FC1D does not service COP or return. */
PcmStatus pcm_illegal_trap(Pcm *pcm)
{
    SYS_RUN(sys_update(pcm,0,0,0x10));return PCM_HALT_BOUNDARY;
}
