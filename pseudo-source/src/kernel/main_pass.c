#include "scheduler.h"
#define RUN(call) do { PcmStatus result = (call); if (result != PCM_OK) return result; } while (0)
/* Reference 7989..7A51. Busy ownership is handled by dispatcher.c. */
PcmStatus pcm_main_pass(Pcm *pcm)
{
    if (pcm->runtime.engine_service && pcm->runtime.service_output_enable)
        pcm->runtime.service_output_mirror = pcm->runtime.service_output_value;
    RUN(pcm_phase_advance(pcm));
    RUN(pcm_mask_irq(pcm, true));
    pcm->runtime.monitor_freeze = pcm->runtime.ignition_off ||
        pcm->runtime.engine_service || pcm->runtime.transmission_service;
    RUN(pcm_mask_irq(pcm, false));
    RUN(pcm_dispatch_fast(pcm));
    return pcm_dispatch_slot(pcm);
}
