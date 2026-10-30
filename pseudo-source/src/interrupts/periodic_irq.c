#include "scheduler.h"
#include "hardware.h"
#define RUN(call) do { PcmStatus result = (call); if (result != PCM_OK) return result; } while (0)

/* Reference 793D..7989. Actual interrupt entry/RTI and SP recovery need target
 * assembly. This routine assumes the platform supplies those boundary rules. */
PcmStatus pcm_periodic_irq(Pcm *pcm)
{
    if (pcm->calibration == NULL || pcm->calibration->recurring_compare_counts == 0)
        return PCM_BAD_CONFIGURATION;
    uint16_t old_compare;
    RUN(pcm_read16(pcm, PCM_TOC3, &old_compare));
    RUN(pcm_write16(pcm, PCM_TOC3,
        (uint16_t)(old_compare + pcm->calibration->recurring_compare_counts)));
    RUN(pcm_write8(pcm, PCM_TFLG1, 0x20));
    pcm->scheduler.timer_seen = true;
    if (pcm->runtime.factory_mode) return PCM_FACTORY_BOUNDARY;
    RUN(pcm_mask_irq(pcm, false));
    if (pcm->platform->check_stack == NULL) return PCM_STACK_BOUNDARY;
    RUN(pcm->platform->check_stack(pcm->platform->context, pcm->scheduler.busy));
    RUN(pcm_fast_service(pcm));
    if (pcm->scheduler.busy) {
        pcm->scheduler.busy_phase = pcm->scheduler.phase;
        pcm->scheduler.pending = true;
        return PCM_OK;
    }
    return pcm_dispatcher(pcm);
}
