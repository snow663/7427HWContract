#include "hardware.h"
/* 785A..7874. A latched diagnostic does not identify a physical bank fault. */
PcmStatus pcm_reference_bank_guard(Pcm *pcm)
{
    const PcmReferenceCalibration *cal = &pcm->calibration->reference;
    if (cal->diagnostic_options & 0x40u) {
        if (pcm->reference.bank_guard_count != 255) ++pcm->reference.bank_guard_count;
        if (pcm->reference.bank_guard_count > cal->bank_guard_limit) pcm->reference.bank_fault = true;
    }
    return PCM_OK;
}
