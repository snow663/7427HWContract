#include "control.h"
#include "iac.h"
#define RUN(call) do { PcmStatus result = (call); if (result != PCM_OK) return result; } while (0)
/* 93D0..989B. Optional1803 precedes every resident effect. */
PcmStatus pcm_iac_control(Pcm *pcm)
{
    if (pcm->scheduler.profiling_enabled) RUN(pcm_run_task(pcm, PCM_IAC_EXTENSION));
    pcm->iac.transfer_flags &= (uint8_t)~0x40u;
    if (pcm->runtime.engine_service) {
        bool exited;
        RUN(pcm_iac_service(pcm, &exited));
        if (exited) return PCM_OK;
    }
    if (pcm->iac.state_flags & 1u) {
        pcm->iac.target = 0;
        if (pcm->iac.position != 0) return PCM_OK;
        pcm->iac.state_flags = (uint8_t)((pcm->iac.state_flags & (uint8_t)~1u) | 4u);
        RUN(pcm_iac_seed_cells(pcm));
    }
    if (pcm->reference.latch_inhibited) {
        if (!(pcm->iac.state_flags & 4u)) return pcm_iac_reset_request(pcm);
        if (pcm->calibration == NULL || pcm->calibration->iac == NULL) return PCM_BAD_CONFIGURATION;
        pcm->iac.target = pcm->calibration->iac->park_target;
        return PCM_OK;
    }
    if (!pcm->runtime.spark_running) return pcm_iac_start(pcm);
    RUN(pcm_iac_context(pcm));
    RUN(pcm_iac_error(pcm));
    RUN(pcm_iac_integral(pcm));
    RUN(pcm_iac_proportional(pcm));
    RUN(pcm_iac_derivative(pcm));
    return pcm_iac_compose(pcm);
}
