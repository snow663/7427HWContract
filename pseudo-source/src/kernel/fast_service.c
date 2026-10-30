#include "scheduler.h"
#include "hardware.h"
#include "control.h"
#define RUN(call) do { PcmStatus result = (call); if (result != PCM_OK) return result; } while (0)
/* Reference 7B6D..7BA6. Runs before the busy test, including busy reentry. */
PcmStatus pcm_fast_service(Pcm *pcm)
{
    RUN(pcm_iac_step(pcm));
    /* This dependency owns the intervening ADC/F245 acquisition sequence. */
    RUN(pcm_adc_feedback(pcm));
    RUN(pcm_current_control(pcm));
    return pcm_write16(pcm, PCM_CURRENT_COMMAND, (uint16_t)(0x0600u | pcm->runtime.current_output));
}
