#include "control.h"
#include "../system/system_internal.h"
/*E6E5..E6F4. Distinct mask E756..E75E publishes only0099.4. */
PcmStatus pcm_fault_injection_reaction(Pcm *pcm)
{
    uint8_t value;SYS_RUN(pcm_fault_reaction_mask(pcm,0xe755,&value));
    return sys_update(pcm,0x0099,value?0:0x10,value?0x10:0);
}
