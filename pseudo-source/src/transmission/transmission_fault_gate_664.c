#include "control.h"
#include "../system/system_internal.h"

/* $E664..$E673. Publish the E728 mask scan into $0098.5. */
PcmStatus pcm_transmission_fault_gate_664(Pcm *pcm)
{
    bool active;
    SYS_RUN(pcm_transmission_mask_scan(pcm, 0xe728, &active));
    return pcm_update8(pcm, 0x98, 0x20, active ? 0x20 : 0);
}
