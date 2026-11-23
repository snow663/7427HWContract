#include "gear_internal.h"
/* BMHM E69C..E6AB: E73A mask drives 0099.0, with no unrelated bits
 * cleared and no write before completion of the nine-entry scan. */
PcmStatus pcm_transmission_fault_gate_69c(Pcm *pcm)
{
    if (pcm == NULL) return PCM_BAD_CONFIGURATION;
    bool fault;
    PcmStatus result = pcm_transmission_mask_scan(pcm, 0xe73au, &fault);
    if (result != PCM_OK) return result;
    return gear_publish_fault_bit(pcm, 0x01u, fault);
}
