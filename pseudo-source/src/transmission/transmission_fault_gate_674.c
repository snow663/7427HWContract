#include "control.h"
#include "hardware.h"
#include "../system/system_internal.h"

/* E674..E683. The fault gate stores the result before its caller reads 0098.6. */
PcmStatus pcm_transmission_fault_gate_674(Pcm *pcm)
{
    bool active;
    SYS_RUN(pcm_transmission_mask_scan(pcm, 0xe731, &active));
    return pcm_update8(pcm, 0x98, 0x40, active ? 0x40 : 0);
}
