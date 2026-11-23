#include "slot_d_internal.h"

static PcmStatus toggle_lamp(Pcm *pcm)
{
    uint8_t flags;
    D_READ(0x72, flags);
    return d_update(pcm, 0x72, 0x80, flags & 0x80u ? 0 : 0x80);
}

/* DCB0..DCE9. Open loop alternates 0043.6. Closed loop uses the
 * coarse phase strobe and 003E.6 to drive the indicator. */
static PcmStatus running_display(Pcm *pcm)
{
    uint8_t flags;
    if (pcm->io.coolant_context & 0x80u) {
        D_READ(0x43, flags);
        if (flags & 8u) {
            D_READ(0x6f, flags);
            if (!(flags & 0x80u)) return PCM_OK;
            D_READ(0x43, flags);
            if (flags & 0x10u) {
                D_CLEAR(0x43, 0x10);
                return toggle_lamp(pcm);
            }
            return d_update(pcm, 0x72, 0x80, pcm->io.coolant_context & 0x40u ? 0x80 : 0);
        }
        D_READ(0x6f, flags);
        if (flags & 0x80u) {
            D_SET(0x43, 8);
            return d_update(pcm, 0x72, 0x80, pcm->io.coolant_context & 0x40u ? 0x80 : 0);
        }
    }
    D_READ(0x43, flags);
    flags = (uint8_t)((flags & (uint8_t)~8u) ^ 0x40u);
    D_STORE(0x43, flags);
    if (flags & 0x40u) return PCM_OK;
    return toggle_lamp(pcm);
}

static PcmStatus age_history(Pcm *pcm)
{
    uint8_t flags, age, checksum, limit;
    D_READ(0x43, flags);
    if ((flags & 2u) || (uint8_t)pcm->scheduler.run_counter < 10u) return PCM_OK;
    D_SET(0x43, 2);
    D_COUNT(0x14, 1, age);
    D_COUNT(0x15, -1, checksum);
    D_READ(0x14, age);
    D_READ(0x5b12, limit);
    if (age <= limit) return PCM_OK;
    for (uint16_t i = 9; i != 0; --i) D_STORE((uint16_t)(0x0a + i), 0);
    D_STORE(0x14, 0);
    D_STORE(0x3c, 0);
    SYS_RUN(pcm_diagnostic_checksum(pcm, &checksum));
    return d_store(pcm, 0x15, checksum);
}

/* DC89..E1EB. Service-switch, stopped-engine and special-mode exits
 * are distinct. Only eligible running calls execute the monitor chain. */
PcmStatus pcm_diagnostic_slot_d(Pcm *pcm)
{
    if (pcm == NULL || pcm->calibration == NULL) return PCM_BAD_CONFIGURATION;
    D_SET(0x6f, 0x80);
    if (pcm->scheduler.phase & 0xf0u) D_CLEAR(0x6f, 0x80);
    if (pcm->runtime.diagnostic_switch) {
        D_SET(0x71, 0x80);
        D_STORE(0x022b, 0);
        if (!pcm->runtime.spark_running) {
            D_CLEAR(0x43, 0x1c);
            goto stopped;
        }
        SYS_RUN(running_display(pcm));
        D_STORE(0x3c, 0);
        D_STORE(0x0216, 0);
        D_SET(0x43, 4);
    } else {
        D_CLEAR(0x71, 0x80);
        D_CLEAR(0x43, 0x1c);
        D_STORE(0x3c, 0);
        D_STORE(0x0216, 0);
        if (pcm->runtime.special_fast_group) return d_update(pcm, 0x72, 0, 0x80);
        if (!pcm->runtime.spark_running) goto stopped;
    }
    SYS_RUN(age_history(pcm));
    SYS_RUN(pcm_diagnostic_engine_inputs(pcm));
    SYS_RUN(pcm_diagnostic_egr_test(pcm));
    SYS_RUN(pcm_diagnostic_engine_feedback(pcm));
    return pcm_diagnostic_report(pcm);
stopped:
    D_STORE(0x0228, 0);
    D_STORE(0x0219, 0);
    SYS_RUN(pcm_write16(pcm, 0x021a, 0));
    return pcm_diagnostic_report(pcm);
}
