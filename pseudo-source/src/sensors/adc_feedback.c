#include "control.h"
/* Reference 7B6D: Intervening ADC acquisition F245 and averaged014E publication.
 * Contract boundary: body not ported. An explicit platform binding is required. */
PcmStatus pcm_adc_feedback(Pcm *pcm)
{
    return pcm_run_task(pcm, PCM_ADC_FEEDBACK);
}
