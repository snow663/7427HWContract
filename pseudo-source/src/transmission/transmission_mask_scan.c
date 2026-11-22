#include "control.h"
/* BMHM $E6BC..$E6E3. The 68HC11 indexes nine status bytes in descending
 * order, reading $5B33+B (alternate suppress), $5B2A+B (enabled mask),
 * $0015+B (active diagnostic bits), and (table+B) in that exact order.
 * Stop at the first nonzero intersection; do not optimize the four reads
 * into a speculative short-circuit (peripheral failure order matters).
 * This helper returns only the source TSTA Z interpretation, not flags. */
PcmStatus pcm_transmission_mask_scan(Pcm *pcm, uint16_t table, bool *active)
{
    if (pcm == NULL || active == NULL) return PCM_BAD_CONFIGURATION;
    for (unsigned index = 9u; index >= 1u; --index) {
        uint8_t alternate, enabled, fault, table_mask;
        PcmStatus status = pcm_read8(pcm, (uint16_t)(0x5b33u+index), &alternate);
        if (status != PCM_OK) return status;
        status = pcm_read8(pcm, (uint16_t)(0x5b2au+index), &enabled);
        if (status != PCM_OK) return status;
        status = pcm_read8(pcm, (uint16_t)(0x0015u+index), &fault);
        if (status != PCM_OK) return status;
        status = pcm_read8(pcm, (uint16_t)(table+index), &table_mask);
        if (status != PCM_OK) return status;
        if (((uint8_t)(~alternate) & enabled & fault & table_mask) != 0u) {
            *active = true;
            return PCM_OK;
        }
    }
    *active = false;
    return PCM_OK;
}
