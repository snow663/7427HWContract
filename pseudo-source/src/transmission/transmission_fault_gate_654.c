#include "control.h"
#include "../system/system_internal.h"

/* $E654..$E663. E6BC scans the nine diagnostic banks with the E71F mask. */
PcmStatus pcm_transmission_fault_gate_654(Pcm *pcm)
{
    bool active;
    SYS_RUN(pcm_transmission_mask_scan(pcm, 0xe71f, &active));
    return pcm_update8(pcm, 0x98, 0x10, active ? 0x10 : 0);
}
