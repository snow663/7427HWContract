#include "iac.h"
#define RUN(call) do { PcmStatus result = (call); if (result != PCM_OK) return result; } while (0)
/* A2B0..A406. Nonrunning returns before all work; phase bit5 gates both the
 * later learning diagnostic and reset admission, after the earlier updates. */
PcmStatus pcm_iac_slow(Pcm *pcm)
{
    if (!pcm->runtime.spark_running) return PCM_OK;
    RUN(pcm_iac_follower(pcm));
    RUN(pcm_iac_slow_decays(pcm));
    RUN(pcm_iac_drive_limit(pcm));
    RUN(pcm_iac_kicker_diagnostic(pcm));
    if (pcm->scheduler.phase & 0x20u) return PCM_OK;
    RUN(pcm_iac_learning_diagnostic(pcm));
    return pcm_iac_reset_admit(pcm);
}
