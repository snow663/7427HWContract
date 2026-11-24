#include "slot_d_internal.h"

/* DD40..DDB9. The old O2 timer can set code 13 before current TPS is examined. */
static PcmStatus oxygen_activity(Pcm *pcm)
{
    uint8_t flags, limit, age;
    D_CLEAR(0x16, 0x80);
    D_READ(0x6f, flags);
    if (flags & 0x24u) goto clear;
    D_READ(0x71, flags);
    if (!(flags & 0x40u)) {
        uint8_t half_time = (uint8_t)(pcm->scheduler.run_counter >> 1);
        D_READ(0x4e32, limit);
        if (half_time < limit) goto clear;
        D_SET(0x71, 0x40);
    }
    D_READ(0x015f, age);
    if (pcm->runtime.deceleration_fuel_cut) {
        D_READ(0x4e33, limit);
        if (age < limit) D_COUNT(0x015f, 1, age);
        goto clear;
    }
    if (age) --age;
    D_STORE(0x015f, age);
    D_READ(0x4e34, limit);
    if (age >= limit) goto clear;
    uint8_t sample = pcm->fuel.raw_oxygen;
    D_READ(0x4e36, limit);
    if (sample > limit) goto clear;
    D_READ(0x4e35, limit);
    if (sample <= limit) goto clear;
    D_READ(0x021c, age);
    D_READ(0x4e38, limit);
    if (age > limit) return d_update(pcm, 0x16, 0, 0x80);
    if ((pcm->scheduler.phase & 0xf0u) || (pcm->scheduler.run_counter & 1u)) return PCM_OK;
    sample = pcm->reference.coolant;
    D_READ(0x4e39, limit);
    if (sample <= limit) return PCM_OK;
    sample = pcm->reference.throttle;
    D_READ(0x4e37, limit);
    if (sample > limit) D_COUNT(0x021c, 1, age);
    else {
        D_READ(0x021c, age);
        if (age) D_COUNT(0x021c, -1, age);
    }
    return PCM_OK;
clear:
    return d_store(pcm, 0x021c, 0);
}

static PcmStatus code16(Pcm *pcm)
{
    uint8_t flags, age, limit, sample;
    D_CLEAR(0x16, 0x10);
    D_READ(0x6f, flags);
    if (flags & 0x48u) goto clear;
    sample = pcm->spark.vehicle_speed_high;
    D_READ(0x4e3a, limit);
    if (sample > limit) goto clear;
    D_READ(0x0817, age);
    D_READ(0x4e3f, limit);
    if (age > limit) return d_update(pcm, 0x16, 0, 0x10);
    sample = pcm->spark.map_filtered;
    D_READ(0x4e3d, limit);
    if (sample >= limit) goto clear;
    sample = pcm->reference.coolant;
    D_READ(0x4e3e, limit);
    if (sample <= limit) goto clear;
    sample = pcm->reference.rpm_coordinate;
    D_READ(0x4e3b, limit);
    if (sample <= limit) goto clear;
    D_READ(0x4e3c, limit);
    if (sample > limit) goto clear;
    sample = pcm->reference.throttle;
    D_READ(0x4e40, limit);
    if (sample >= limit) goto clear;
    D_READ(0x6f, flags);
    if (flags & 0x80u) D_COUNT(0x0817, 1, age);
    return PCM_OK;
clear:
    return d_store(pcm, 0x0817, 0);
}

static PcmStatus speed_signal(Pcm *pcm)
{
    uint8_t flags, age, limit;
    if (!(pcm->calibration->mode_f & 0x80u)) return PCM_OK;
    D_READ(0x5b01, flags);
    if (!(flags & 0x20u)) return PCM_OK;
    if (pcm->transmission.shift_delta) {
        D_CLEAR(0x17, 0x20);
        return d_store(pcm, 0x081c, 0);
    }
    D_READ(0x081c, age);
    D_READ(0x4e43, limit);
    if (age > limit) return d_update(pcm, 0x17, 0, 0x20);
    uint8_t speed = pcm->spark.vehicle_speed_high;
    D_READ(0x4e44, limit);
    if (speed > limit) D_COUNT(0x081c, 1, age);
    return PCM_OK;
}

/* DD40..DE55, the engine signal, vehicle speed and governor monitors. */
PcmStatus pcm_diagnostic_engine_inputs(Pcm *pcm)
{
    if (pcm == NULL || pcm->calibration == NULL) return PCM_BAD_CONFIGURATION;
    SYS_RUN(oxygen_activity(pcm));
    SYS_RUN(code16(pcm));
    SYS_RUN(speed_signal(pcm));
    D_CLEAR(0x18, 0x80);
    if (pcm->calibration->mode_f & 1u) {
        uint8_t flags, limit;
        D_READ(0x6f, flags);
        if (!(flags & 0x10u)) {
            uint8_t high = (uint8_t)(pcm->transmission.governor_integrator >> 8);
            D_READ(0x4e4b, limit);
            if (high < limit) return PCM_OK;
        }
        D_SET(0x18, 0x80);
        D_SET(0x6f, 0x10);
    }
    return PCM_OK;
}
