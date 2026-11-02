#include "fuel.h"
#include "feedback_internal.h"
#include "hardware.h"
/*88CD..88E8. Both comparisons around the P window are strict. */
PcmStatus pcm_oxygen_window(Pcm *pcm, uint8_t window)
{
    FB_CAL();
    uint8_t age = pcm->fuel.oxygen_direction_age;
    if ((age > window && age < mix_byte((unsigned)window+cal->window_width)) || pcm->fuel.warmup_control) pcm->fuel.proportional = 0;
    return PCM_OK;
}
