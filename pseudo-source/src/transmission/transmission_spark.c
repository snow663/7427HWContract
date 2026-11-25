#include "control.h"
#include "board_io.h"
#include "../system/system_internal.h"

/* $C4E5..$C4F4. Each stage consumes the preceding stage's committed state. */
PcmStatus pcm_transmission_spark(Pcm *pcm)
{
    SYS_RUN(pcm_transmission_throttle(pcm));
    SYS_RUN(pcm_transmission_spark_mode(pcm));
    SYS_RUN(pcm_transmission_range_retard(pcm));
    SYS_RUN(pcm_transmission_shift_retard(pcm));
    return pcm_transmission_spark_coolant(pcm);
}
