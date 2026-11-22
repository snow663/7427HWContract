#include "scheduler.h"
#include "control.h"
#include "fuel.h"
#include "../system/system_internal.h"
/*7B60..7B6C: callable suffix after the C514/C4F5 prefix. The whole slotF
 * dependency stays explicit until that preceding diagnostic group is ported. */
PcmStatus pcm_slot_0f_finish(Pcm *pcm)
{
    SYS_RUN(pcm_fault_primary_reaction(pcm));SYS_RUN(pcm_fault_injection_reaction(pcm));
    SYS_RUN(pcm_fuel_slow(pcm));pcm->runtime.refresh_requested=true;return PCM_OK;
}
