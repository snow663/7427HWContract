#include "scheduler.h"
#include "board_io.h"
#include "service.h"
#include "control.h"
#include "../system/system_internal.h"

/* 7B48..7B51. Diagnostics observe the new MAT sample and live fault bits. */
PcmStatus pcm_slot_0d(Pcm *pcm)
{
    if (pcm == NULL) return PCM_BAD_CONFIGURATION;
    SYS_RUN(pcm_air_shared_outputs(pcm));
    SYS_RUN(pcm_mat_input(pcm));
    return pcm_diagnostic_slot_d(pcm);
}
