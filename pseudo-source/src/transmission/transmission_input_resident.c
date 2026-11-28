#include "resident_input_private_3.h"

/* AE85 prefix only. The existing F781/F64E service tail remains
 * canonical and is a separate joined-entry verification obligation. */
PcmStatus pcm_transmission_input_resident(Pcm *pcm)
{
    SYS_RUN(pcm_resident_input_aea4(pcm));
    SYS_RUN(pcm_resident_input_b018(pcm));
    SYS_RUN(pcm_resident_input_b089(pcm));
    SYS_RUN(pcm_resident_input_c483(pcm));
    SYS_RUN(pcm_resident_input_b1f0(pcm));
    SYS_RUN(pcm_resident_input_b23c(pcm));
    SYS_RUN(pcm_resident_speed_ratio(pcm));
    return pcm_resident_temperature_class(pcm);
}
