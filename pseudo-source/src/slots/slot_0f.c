#include "scheduler.h"
#include "control.h"
#include "../system/system_internal.h"
/* 7B5A..7B6C, table word7AA3: outputs precede the diagnostic observations;
 * fault reactions and slow fuel consume those observations before refresh. */
PcmStatus pcm_slot_0f(Pcm *pcm)
{
    SYS_RUN(pcm_transmission_outputs(pcm));SYS_RUN(pcm_diagnostic_slot_f(pcm));
    return pcm_slot_0f_finish(pcm);
}
