#include "interrupts.h"
#include "../system/system_internal.h"
/*74EE ->FC11..FC18. Record factory REF and acknowledge IC3; no fuel work. */
PcmStatus pcm_factory_reference_irq(Pcm *pcm)
{
    SYS_RUN(sys_update(pcm,0,0,2));return pcm_write8(pcm,PCM_TFLG1,1);
}
