#include "startup.h"
#define RUN(call) do { PcmStatus result = (call); if (result != PCM_OK) return result; } while (0)

/* Coarse ordinary-boot outline. Reset SP/CCR, vectors, early unmasking and
 * factory/trap alternatives must be handled by the future target backend.
 * No stage is considered implemented simply because it has a filename. */
PcmStatus pcm_reset_sequence(Pcm *pcm, const PcmPlatform *platform, const PcmCalibration *calibration)
{
    if (pcm == NULL || platform == NULL || calibration == NULL ||
        calibration->format_version != 1 || calibration->initial_phase >= 0xa0 ||
        calibration->recurring_compare_counts == 0 || calibration->first_compare_counts == 0)
        return PCM_BAD_CONFIGURATION;
    pcm->platform = platform;
    pcm->calibration = calibration;
    pcm->scheduler = (PcmScheduler){0};
    pcm->runtime = (PcmRuntime){0};
    pcm->application = NULL;
    pcm->unresolved_task = PCM_TASK_COUNT;
    RUN(pcm_mask_irq(pcm, true));
    RUN(pcm_reset_cpu(pcm));
    RUN(pcm_reset_outputs(pcm));
    RUN(pcm_reset_ram(pcm));
    RUN(pcm_reset_sensors(pcm));
    if (pcm->runtime.factory_mode) return PCM_FACTORY_BOUNDARY;
    RUN(pcm_reset_retained(pcm));
    RUN(pcm_reset_controllers(pcm));
    pcm->scheduler.phase = calibration->initial_phase;
    RUN(pcm_reset_serial(pcm));
    return pcm_timer_arm(pcm);
}
