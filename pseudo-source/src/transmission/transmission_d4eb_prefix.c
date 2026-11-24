#include "control.h"
#include "hardware.h"
/* Stock D4EB..D4F7 entrance: three E6xx diagnostic producers, then
 * CLRA / STAA 0084 before the D4F7 gear selector. Deliberately scoped
 * to this completed prefix. Do not call it before handing off to the
 * ORIGINAL D4EB entry: that would duplicate diagnostics and state writes. */
PcmStatus pcm_transmission_d4eb_prefix(Pcm *pcm)
{
    if (pcm == NULL) return PCM_BAD_CONFIGURATION;
    PcmStatus result = pcm_transmission_fault_gate_684(pcm);
    if (result != PCM_OK) return result;
    result = pcm_transmission_fault_gate_6ac(pcm);
    if (result != PCM_OK) return result;
    result = pcm_transmission_fault_gate_69c(pcm);
    if (result != PCM_OK) return result;
    return pcm_write8(pcm, 0x0084u, 0u);
}
