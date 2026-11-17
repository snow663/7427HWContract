#include "scheduler.h"
#include "hardware.h"
#include "interrupts.h"
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
    if (pcm->runtime.factory_mode) {
        ++pcm->scheduler.phase; /*7952 increments the raw byte before FA5B. */
        return PCM_FACTORY_BOUNDARY;
    }
    RUN(pcm_mask_irq(pcm, false));
    /* A future target entry shim may provide the X captured at $7959.
     * Preserve the legacy host check_stack boundary when that ABI is absent. */
    if (pcm->platform != NULL && pcm->platform->capture_timer_stack_x != NULL) {
        uint16_t captured_x;
        RUN(pcm->platform->capture_timer_stack_x(pcm->platform->context,&captured_x));
        bool reset_required=false;
        RUN(pcm_timer_stack_guard(pcm,captured_x,&reset_required));
        if (reset_required) return PCM_STACK_RECOVERY_BOUNDARY;
    } else {
        if (pcm->platform == NULL || pcm->platform->check_stack == NULL)
            return PCM_STACK_BOUNDARY;
        RUN(pcm->platform->check_stack(pcm->platform->context, pcm->scheduler.busy));
    }
    return pcm_periodic_irq_resume(pcm);
}
