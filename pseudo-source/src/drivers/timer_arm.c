#include "hardware.h"
/* Reference 745E..7469: first TCNT-relative arm; recurrence is TOC3-relative. */
PcmStatus pcm_timer_arm(Pcm *pcm)
{
    if (pcm->calibration == NULL || pcm->calibration->first_compare_counts == 0)
        return PCM_BAD_CONFIGURATION;
    uint16_t counter;
    PcmStatus result = pcm_read16(pcm, PCM_TCNT, &counter);
    if (result != PCM_OK) return result;
    result = pcm_write16(pcm, PCM_TOC3, (uint16_t)(counter + pcm->calibration->first_compare_counts));
    if (result != PCM_OK) return result;
    /* Stock pair OC1/OC3. Changing enabled sources is a deliberate later port. */
    return pcm_write8(pcm, PCM_TMSK1, 0xa0);
}
