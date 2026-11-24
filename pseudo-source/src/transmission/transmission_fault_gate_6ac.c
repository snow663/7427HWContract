#include "gear_internal.h"
/* BMHM E6AC..E6BB: E743 mask drives 0099.1. Stock D4EB calls
 * E684, E6AC, E69C (not numeric order). */
PcmStatus pcm_transmission_fault_gate_6ac(Pcm *pcm)
{
    if (pcm == NULL) return PCM_BAD_CONFIGURATION;
    bool fault;
    PcmStatus result = pcm_transmission_mask_scan(pcm, 0xe743u, &fault);
    if (result != PCM_OK) return result;
    return gear_publish_fault_bit(pcm, 0x02u, fault);
}
