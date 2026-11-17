#include "pcm.h"
#include "control.h"
/* The spark suites predate the new resident D14E..D1F5 EGR feedback
 * acquisition. Preserve their pre-existing dependency trace instead of
 * admitting real ADC/lag reads from the new controller-boot port. The
 * controller-boot suite links the actual implementation and ROM checks it. */
PcmStatus pcm_egr_feedback(Pcm *pcm)
{
    return pcm_run_task(pcm,PCM_EGR_FEEDBACK);
}
