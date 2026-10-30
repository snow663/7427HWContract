#include "scheduler.h"
/* Reference 798C..79C5. Counts admitted passes, not every timer arrival. */
PcmStatus pcm_phase_advance(Pcm *pcm)
{
    uint8_t next = (uint8_t)(pcm->scheduler.phase + 1u);
    if (next == 0xa0) {
        next = 0;
        pcm->scheduler.epoch_toggle = !pcm->scheduler.epoch_toggle;
        if (pcm->runtime.spark_running) {
            uint16_t temporary = (uint16_t)(pcm->scheduler.run_counter + 1u);
            if (temporary != 0) pcm->scheduler.run_counter = temporary;
            /* At FFFF the stored value remains FFFF; comparison uses zero. */
            if (temporary >= pcm->calibration->run_counter_clear_threshold)
                pcm->scheduler.clear_after_run_count = false;
        }
    }
    pcm->scheduler.phase = next;
    return PCM_OK;
}
