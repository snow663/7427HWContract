#include "slot_d_internal.h"
#include "fuel.h"

static PcmStatus map_high(Pcm *pcm)
{
    uint8_t flags, limit, age;
    D_CLEAR(0x18, 0x20);
    D_READ(0x6f, flags);
    flags &= (uint8_t)~0x40u;
    if (flags & 0x24u) goto clear;
    D_READ(0x4e61, limit);
    if (limit > pcm->spark.barometric_high) limit = pcm->spark.barometric_high;
    if (limit >= pcm->reference.map_sample) goto clear;
    D_READ(0x0228, age);
    D_READ(0x4e62, limit);
    if (age > limit) {
        D_SET(0x18, 0x20);
        flags |= 0x40u;
    } else {
        uint8_t sample = pcm->reference.throttle;
        D_READ(0x4e60, limit);
        if (sample >= limit) goto clear;
        sample = pcm->spark.rpm_low_coordinate;
        D_READ(0x4e63, limit);
        if (sample < limit) goto clear;
        D_COUNT(0x0228, 1, age);
    }
    return d_store(pcm, 0x6f, flags);
clear:
    D_STORE(0x0228, 0);
    return d_store(pcm, 0x6f, flags);
}

static PcmStatus est_counter(Pcm *pcm)
{
    if (pcm->runtime.output_override || pcm->io.diagnostic_warm ||
        (pcm->scheduler.phase & 0x10u) || !pcm->spark.startup_gain_enabled) return PCM_OK;
    uint16_t sample;
    uint8_t age = 0, limit;
    SYS_RUN(pcm_read16(pcm, PCM_EST_COUNTER, &sample));
    uint8_t rpm = pcm->spark.rpm_low_coordinate;
    D_READ(0x4e70, limit);
    if (rpm > limit && sample == pcm->spark.bypass_baseline) {
        age = pcm->spark.bypass_count;
        D_READ(0x4e73, limit);
        if (age > limit) D_SET(4, 0x80);
        else ++age;
    }
    D_STORE(0x022c, age);
    SYS_RUN(pcm_write16(pcm, 0x0205, sample));
    pcm->spark.bypass_baseline = sample;
    return PCM_OK;
}

static PcmStatus lean_oxygen(Pcm *pcm)
{
    uint8_t limit, sample, age, flags;
    D_CLEAR(0x19, 8);
    D_READ(0x4e78, limit);
    D_READ(0x01d0, sample);
    if (limit <= sample) goto reset;
    D_READ(0x0219, age);
    D_READ(0x72, flags);
    if (flags & 0x40u) {
        D_READ(0x4e7a, limit);
        if (age > limit) return d_update(pcm, 0x19, 0, 8);
        if (pcm->scheduler.run_counter & 1u) return PCM_OK;
    } else {
        D_READ(0x4e79, limit);
        if (age > limit) {
            D_SET(0x72, 0x40);
            return d_store(pcm, 0x0219, 0);
        }
        if (!(pcm->io.coolant_context & 0x80u)) goto reset;
        D_READ(0x71, flags);
        if (flags & 4u) goto reset;
    }
    D_READ(0x6f, flags);
    if (flags & 0x80u) D_COUNT(0x0219, 1, age);
    return PCM_OK;
reset:
    D_CLEAR(0x72, 0x40);
    return d_store(pcm, 0x0219, 0);
}

static PcmStatus rich_oxygen(Pcm *pcm)
{
    uint8_t sample, limit, flags;
    if (!(pcm->calibration->reference.mode_e & 0x20u)) D_CLEAR(0x19, 4);
    D_READ(0x01d0, sample);
    D_READ(0x4e7d, limit);
    if (sample <= limit) goto clear;
    uint16_t age, maximum;
    SYS_RUN(pcm_read16(pcm, 0x021a, &age));
    D_READ(0x44, flags);
    uint16_t limit_address = 0x4e80;
    if (!(flags & 0x20u)) {
        sample = pcm->spark.mat_sample;
        D_READ(0x4e7c, limit);
        if (sample > limit) D_SET(0x44, 0x20);
        else limit_address = 0x4e7e;
    }
    SYS_RUN(pcm_read16(pcm, limit_address, &maximum));
    if (age > maximum) return d_update(pcm, 0x19, 0, 4);
    if (!(pcm->io.coolant_context & 0x80u)) goto clear;
    D_READ(0x71, flags);
    if (flags & 4u) goto clear;
    sample = pcm->reference.throttle;
    D_READ(0x4e82, limit);
    if (sample <= limit) {
        D_READ(0x4e83, limit);
        if (sample >= limit) goto clear;
    }
    D_READ(0x6f, flags);
    if (flags & 0x80u) {
        SYS_RUN(pcm_read16(pcm, 0x021a, &age));
        return pcm_write16(pcm, 0x021a, (uint16_t)(age + 1u));
    }
    return PCM_OK;
clear:
    return pcm_write16(pcm, 0x021a, 0);
}

/* DFCA..E119, including the conditional 21-cell F28E clamp. */
PcmStatus pcm_diagnostic_engine_feedback(Pcm *pcm)
{
    if (pcm == NULL || pcm->calibration == NULL) return PCM_BAD_CONFIGURATION;
    SYS_RUN(map_high(pcm));
    SYS_RUN(est_counter(pcm));
    SYS_RUN(lean_oxygen(pcm));
    SYS_RUN(rich_oxygen(pcm));
    D_CLEAR(0x71, 4);
    uint8_t flags, age, limit;
    if (pcm->calibration->reference.mode_c & 2u) {
        D_READ(0x19, flags);
        bool clamp = (flags & 4u) != 0;
        if (!clamp) {
            D_READ(0x72, flags);
            clamp = (flags & 0x40u) != 0;
        }
        if (clamp) SYS_RUN(pcm_blm_boot_clamp(pcm));
    }
    D_READ(0x5b03, flags);
    if (!(flags & 2u) || pcm->spark.battery_sample < 90u || pcm->fuel.authorized) return PCM_OK;
    D_READ(0x0856, age);
    D_READ(0x4e84, limit);
    if (age > limit) D_SET(0x19, 2);
    else if (age != 255u) D_STORE(0x0856, (uint8_t)(age + 1u));
    return PCM_OK;
}
