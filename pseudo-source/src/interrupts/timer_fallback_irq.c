#include "interrupts.h"
#include "hardware.h"
/*FC2F..FC38, shared by the FFE6/FFEA/FFEC/FFEE/FFF0 vectors. */
PcmStatus pcm_timer_fallback_irq(Pcm *pcm)
{
    PcmStatus status=pcm_write8(pcm,PCM_TMSK1,0xa0);
    return status==PCM_OK?pcm_write8(pcm,PCM_TFLG1,0x5f):status;
}
