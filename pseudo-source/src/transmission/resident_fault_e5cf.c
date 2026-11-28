#include "resident_input_private_1.h"

/* E5CF..E5F0 */
PcmStatus pcm_resident_fault_e5cf(Pcm *pcm)
{
    bool active;
    SYS_RUN(mask_test(pcm, 0x5b34, 0x5b2b, 0x16, 1, &active));
    if (!active) SYS_RUN(mask_test(pcm, 0x5b35, 0x5b2c, 0x17, 0x80, &active));
    return pcm_update8(pcm, 0x98, 1, active ? 1 : 0);
}
