#include "control.h"
#include "hardware.h"
/* BMHM E684..E69B: 001D.7 takes priority; else only 0087.1 admits
 * the E74C diagnostic-mask scan; final 0098.7 is always assigned. */
PcmStatus pcm_transmission_fault_gate_684(Pcm *pcm)
{
    if (pcm == NULL) return PCM_BAD_CONFIGURATION;
    uint8_t input;
    PcmStatus result = pcm_read8(pcm, 0x001du, &input);
    if (result != PCM_OK) return result;
    bool fault = (input & 0x80u) != 0u;
    if (!fault) {
        result = pcm_read8(pcm, 0x0087u, &input);
        if (result != PCM_OK) return result;
        if ((input & 0x02u) != 0u) {
            result = pcm_transmission_mask_scan(pcm, 0xe74cu, &fault);
            if (result != PCM_OK) return result;
        }
    }
    return pcm_update8(pcm, 0x0098u, 0x80u, fault ? 0x80u : 0u);
}
