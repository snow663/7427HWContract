#include "scheduler.h"
#include "hardware.h"
/* Reference 7A55..7A77. Timer counts, unsigned modulo arithmetic. */
PcmStatus pcm_profile_tail(Pcm *pcm)
{
    if (!pcm->scheduler.profiling_enabled) return PCM_OK;
    uint16_t counter, compare;
    PcmStatus result = pcm_read16(pcm, PCM_TCNT, &counter);
    if (result != PCM_OK) return result;
    result = pcm_read16(pcm, PCM_TOC3, &compare);
    if (result != PCM_OK) return result;
    uint16_t elapsed = (uint16_t)(counter - compare + pcm->calibration->recurring_compare_counts);
    if (pcm->scheduler.pending)
        elapsed = (uint16_t)(elapsed + pcm->calibration->recurring_compare_counts);
    unsigned slot = pcm->scheduler.phase & 15u;
    if (elapsed > pcm->scheduler.peak_counts[slot]) pcm->scheduler.peak_counts[slot] = elapsed;
    return PCM_OK;
}
