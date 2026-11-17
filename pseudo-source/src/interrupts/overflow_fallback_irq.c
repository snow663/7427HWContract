#include "interrupts.h"
#include "hardware.h"
/*FFDA/FFDC/FFDE ->FC3A..FC43. Keep TMSK2/flag2 distinct from TMSK1/flag1. */
PcmStatus pcm_overflow_fallback_irq(Pcm *pcm)
{
    PcmStatus status=pcm_write8(pcm,0x3024,3);
    return status==PCM_OK?pcm_write8(pcm,0x3025,0xff):status;
}
