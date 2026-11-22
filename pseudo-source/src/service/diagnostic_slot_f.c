#include "diagnostic_internal.h"
/* C4F5..C513: order is observable through shared flags and counters. */
PcmStatus pcm_diagnostic_slot_f(Pcm *pcm)
{
    SYS_RUN(pcm_diagnostic_brake_set(pcm));SYS_RUN(pcm_diagnostic_brake_clear(pcm));
    SYS_RUN(pcm_diagnostic_tcc_slip(pcm));SYS_RUN(pcm_diagnostic_top_gear_slip(pcm));
    SYS_RUN(pcm_diagnostic_tcc_released_slip(pcm));SYS_RUN(pcm_diagnostic_current_error(pcm));
    SYS_RUN(pcm_diagnostic_transmission_temperature(pcm));SYS_RUN(pcm_diagnostic_ratio_invalid(pcm));
    SYS_RUN(pcm_diagnostic_ratio_lowgear(pcm));return pcm_diagnostic_ratio_highgear(pcm);
}
