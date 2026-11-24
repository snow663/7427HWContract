#include "slot_d_internal.h"

/* DE56..DF53. Compare the live integrator with its saved value only after
 * the qualification timer has armed the test. Preserve each early exit. */
static PcmStatus integrator_response(Pcm *pcm)
{
    uint8_t flags, sample, limit, timer;
    D_READ(0x5b02, flags);
    if (!(flags & 0x40u)) return PCM_OK;
    D_CLEAR(0x18, 0x40);
    D_READ(0x70, flags);
    if (flags & 8u) return PCM_OK;
    if (pcm->calibration->mode_d & 2u) {
        D_READ(0x70, flags);
        if (flags & 1u) goto publish;
    }
    if (!(pcm->io.coolant_context & 0x80u) || pcm->runtime.deceleration_fuel_cut) goto reload;
    D_READ(0x021f, timer);
    if (timer) {
        D_READ(0x6f, flags);
        if (flags & 0x80u) D_STORE(0x021f, (uint8_t)(timer - 1u));
        goto reset_test;
    }
    D_READ(0x01ae, sample);
    D_READ(0x4e51, limit);
    if (sample < limit) goto reset_test;
    sample = pcm->spark.vacuum;
    D_READ(0x4e4d, limit);
    if (sample <= limit) goto reset_test;
    D_READ(0x4e4e, limit);
    if (sample > limit) goto reset_test;
    sample = pcm->reference.throttle;
    D_READ(0x4e4f, limit);
    if (sample <= limit) goto reset_test;
    D_READ(0x4e50, limit);
    if (sample > limit) goto reset_test;
    uint8_t filtered = (uint8_t)(pcm->fuel.throttle_decel_filter >> 8);
    uint8_t delta = sample >= filtered ? (uint8_t)(sample - filtered) : (uint8_t)(filtered - sample);
    D_READ(0x4e54, limit);
    if (delta > limit) goto reset_test;
    sample = pcm->spark.vehicle_speed_high;
    D_READ(0x4e57, limit);
    if (sample < limit) goto reset_test;
    D_READ(0x6e, flags);
    if (flags & 1u) {
        D_CLEAR(0x6e, 1);
        goto reset_test;
    }
    sample = pcm->fuel.integrator;
    D_READ(0x70, flags);
    if (!(flags & 4u)) {
        delta = sample >= 128u ? (uint8_t)(sample - 128u) : (uint8_t)(128u - sample);
        D_READ(0x48f7, limit);
        if (delta > limit) goto reset_test;
        D_READ(0x0220, timer);
        D_READ(0x4e52, limit);
        if (timer > limit) {
            D_SET(0x70, 4);
            D_STORE(0x0222, pcm->fuel.integrator);
            timer = 0;
        } else ++timer;
        D_STORE(0x0220, timer);
        goto publish;
    }
    uint8_t baseline;
    D_READ(0x0222, baseline);
    if (sample >= baseline) {
        D_READ(0x4e56, limit);
        if (sample - baseline >= limit) {
            uint8_t failures = pcm->io.egr_failure_count;
            if (failures) --failures;
            if (failures) {
                D_STORE(0x0223, failures);
                goto reload;
            }
            D_CLEAR(0x70, 1);
            D_STORE(0x0223, 0);
            if (pcm->calibration->mode_d & 0x80u) D_SET(0x70, 8);
            goto reload;
        }
    }
    D_READ(0x0221, timer);
    D_READ(0x4e55, limit);
    if (timer < limit) {
        D_STORE(0x0221, (uint8_t)(timer + 1u));
        goto publish;
    }
    sample = (uint8_t)(pcm->io.egr_failure_count + 1u);
    D_READ(0x4e53, limit);
    if (sample >= limit) {
        D_SET(0x70, 1);
        --sample;
    }
    D_STORE(0x0223, sample);
reload:
    D_READ(0x4e4c, timer);
    D_STORE(0x021f, timer);
reset_test:
    D_STORE(0x0220, 0);
    D_STORE(0x0221, 0);
    D_CLEAR(0x70, 4);
publish:
    D_READ(0x70, flags);
    if (flags & 1u) D_SET(0x18, 0x40);
    return PCM_OK;
}

/* DF54..DFC9. The feedback and demand checks have separate byte counters.
 * Only the feedback hold at 0225 is a word. */
PcmStatus pcm_diagnostic_egr_test(Pcm *pcm)
{
    if (pcm == NULL || pcm->calibration == NULL) return PCM_BAD_CONFIGURATION;
    SYS_RUN(integrator_response(pcm));
    if (!(pcm->calibration->mode_d & 2u)) return PCM_OK;
    uint8_t flags, sample, limit, timer;
    D_READ(0x5b02, flags);
    if (!(flags & 0x40u)) return PCM_OK;
    D_READ(0x70, flags);
    if (flags & 1u) goto fault;
    D_READ(0x01b4, sample);
    D_READ(0x4e59, limit);
    if (sample < limit) {
        D_READ(0x0227, timer);
        D_READ(0x4e5f, limit);
        if (timer >= limit) {
            D_SET(0x72, 0x20);
            goto latch;
        }
        D_STORE(0x0227, (uint8_t)(timer + 1u));
    } else D_STORE(0x0227, 0);

    D_READ(0x70, flags);
    if (flags & 8u) {
        uint16_t age, maximum;
        SYS_RUN(pcm_read16(pcm, 0x0225, &age));
        SYS_RUN(pcm_read16(pcm, 0x4e5d, &maximum));
        if (age < maximum) return pcm_write16(pcm, 0x0225, (uint16_t)(age + 1u));
        D_CLEAR(0x72, 0x20);
    }
    D_READ(0x01ae, sample);
    D_READ(0x4e5c, limit);
    if (sample > limit) goto clear_timer;
    D_READ(0x01ba, sample);
    D_READ(0x4e5a, limit);
    if (sample <= limit) goto clear_timer;
    D_READ(0x0224, timer);
    D_READ(0x4e5b, limit);
    if (timer < limit) return d_store(pcm, 0x0224, (uint8_t)(timer + 1u));
    D_SET(0x72, 0x20);
    D_READ(0x70, flags);
    if (flags & 8u) goto latch;
    D_SET(0x70, 8);
clear_timer:
    return d_store(pcm, 0x0224, 0);
latch:
    D_SET(0x70, 1);
fault:
    return d_update(pcm, 0x18, 0, 0x40);
}
