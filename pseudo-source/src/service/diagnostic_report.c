#include "slot_d_internal.h"

/* E132..E1C6. The nine pending bytes are intersected with live, enabled
 * faults on subsequent passes. A newly arriving fault waits for reseeding. */
static PcmStatus log_candidates(Pcm *pcm)
{
    uint8_t any = 0, value, enabled, pending, age, flags;
    for (unsigned i = 9; i; --i) {
        D_READ((uint16_t)(0x55 + i), value);
        any |= value;
    }
    if (!any) {
        for (unsigned i = 9; i; --i) {
            D_READ((uint16_t)(0x5aff + i), enabled);
            D_READ((uint16_t)(0x15 + i), value);
            D_STORE((uint16_t)(0x55 + i), (uint8_t)(enabled & value));
        }
        D_READ(0x022b, age);
        if (age) D_COUNT(0x022b, -1, age);
        else D_CLEAR(0x71, 1);
        return PCM_OK;
    }

    any = 0;
    for (unsigned i = 9; i; --i) {
        D_READ((uint16_t)(0x15 + i), value);
        D_READ((uint16_t)(0x55 + i), pending);
        D_READ((uint16_t)(0x5aff + i), enabled);
        D_STORE((uint16_t)(0x55 + i), (uint8_t)(value & pending & enabled));
        D_READ((uint16_t)(0x55 + i), pending);
        any |= pending;
    }
    D_COUNT(0x022b, 1, age);
    D_READ(0x71, flags);
    uint16_t threshold = (uint16_t)(0x4e2e + ((flags & 1u) ? 2u : 0u) + (any ? 1u : 0u));
    D_READ(threshold, value);
    D_READ(0x022b, age);
    if (value >= age) return PCM_OK;
    D_STORE(0x022b, value);
    if (!any) return PCM_OK;
    D_READ(0x4e30, value);
    D_STORE(0x022b, value);
    for (unsigned i = 9; i; --i) {
        D_READ((uint16_t)(0x0a + i), value);
        D_READ((uint16_t)(0x55 + i), pending);
        D_STORE((uint16_t)(0x0a + i), (uint8_t)(value | pending));
        D_STORE((uint16_t)(0x55 + i), 0);
    }
    D_STORE(0x14, 0);
    SYS_RUN(pcm_diagnostic_checksum(pcm, &value));
    D_STORE(0x15, value);
    for (unsigned i = 9; i; --i) {
        D_READ((uint16_t)(0x15 + i), value);
        D_READ((uint16_t)(0x5b08 + i), enabled);
        if (value & enabled) return d_update(pcm, 0x71, 0, 1);
    }
    return PCM_OK;
}

/* E11A..E1EB. E1EC publishes the flash state. Its caller then samples
 * the lamp latch again before making its own final publication. */
PcmStatus pcm_diagnostic_report(Pcm *pcm)
{
    if (pcm == NULL) return PCM_BAD_CONFIGURATION;
    uint8_t flags;
    D_READ(0x43, flags);
    if (flags & 4u) return PCM_OK;
    D_READ(0x71, flags);
    if (flags & 0x80u) SYS_RUN(pcm_diagnostic_flash_codes(pcm));
    else {
        if (pcm->reference.latch_inhibited) return PCM_OK;
        SYS_RUN(log_candidates(pcm));
        if (!pcm->runtime.spark_running) {
            D_READ(0x4f, flags);
            if (flags & 2u) return d_update(pcm, 0x72, 0, 0x80);
            if (!pcm->spark.run_transition) D_SET(0x4f, 2);
            else D_CLEAR(0x4f, 2);
        } else D_CLEAR(0x4f, 2);
        if (pcm->io.diagnostic_warm) return d_update(pcm, 0x72, 0, 0x80);
    }
    D_READ(0x71, flags);
    return d_update(pcm, 0x72, 0x80, (flags & 1u) ? 0x80 : 0);
}
