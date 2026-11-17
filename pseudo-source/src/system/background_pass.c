#include "system_internal.h"
/*746C..74D0. Wake/interrupt entry and74D1's return branch are target control
 * transfers; a host caller resumes with another foreground pass. */
PcmStatus pcm_background_pass(Pcm *pcm)
{
    SYS_RUN(pcm_ram_refresh(pcm));SYS_RUN(pcm_mask_irq(pcm,false));
    SYS_RUN(pcm_stack_watermark(pcm));
    return PCM_BACKGROUND_WAIT_BOUNDARY;
}
