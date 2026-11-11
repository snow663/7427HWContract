#include "startup.h"
/*7459..746B. Acknowledge all TFLG1 flags before the existing TCNT-relative
 * first arm; recurring timer entry remains relative to the previous TOC3. */
PcmStatus pcm_reset_timers(Pcm *pcm)
{
    PcmStatus status=pcm_write8(pcm,PCM_TFLG1,0xff);
    return status==PCM_OK?pcm_timer_arm(pcm):status;
}
