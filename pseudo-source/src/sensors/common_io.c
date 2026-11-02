#include "control.h"
#include "board_io.h"
#define RUN(call) do { PcmStatus result=(call);if (result!=PCM_OK) return result; } while (0)
/* 7BA7..7C12. Keep all four resident admissions in their actual order. */
PcmStatus pcm_common_io(Pcm *pcm)
{
    RUN(pcm_board_latch(pcm));
    RUN(pcm_map_input(pcm));
    RUN(pcm_vss_sample(pcm));
    return pcm_brake_filter(pcm);
}
