#include "pcm.h"
PcmStatus pcm_run_task(Pcm *pcm, PcmTask task)
{
    if ((unsigned)task >= PCM_TASK_COUNT) return PCM_BAD_CONFIGURATION;
    if (pcm->platform == NULL || pcm->platform->task[task] == NULL) {
        pcm->unresolved_task = task;
        return PCM_UNIMPLEMENTED;
    }
    return pcm->platform->task[task](pcm, task);
}
