#include "egr_internal.h"
#include "hardware.h"
#include "reference_math.h"

/* D469/D46E. The AFR limiter consumes this bit through its named owner. */
static PcmStatus rich_request(Pcm *pcm, bool enabled)
{
    SYS_RUN(pcm_update8(pcm, 0x52, enabled ? 0 : 0x40, enabled ? 0x40 : 0));
    pcm->fuel.output_rich_cap = enabled;
    return PCM_OK;
}

static PcmStatus catalyst_request(Pcm *pcm)
{
    uint8_t estimate, limit, age;
    if (pcm->io.coolant_context & 0x80u) {
        SYS_RUN(pcm_read8(pcm, 0x78, &estimate));
        SYS_RUN(pcm_read8(pcm, 0x406d, &limit));
        if (estimate > limit) {
            SYS_RUN(pcm_read8(pcm, 0x084c, &age));
            if (age < 255u) ++age;
            SYS_RUN(pcm_write8(pcm, 0x084c, age));
            SYS_RUN(pcm_read8(pcm, 0x4073, &limit));
            if (age >= limit) return rich_request(pcm, true);
        } else {
            SYS_RUN(pcm_read8(pcm, 0x406e, &limit));
            if (estimate <= limit) goto reset_age;
        }
        SYS_RUN(pcm_read8(pcm, 0x406f, &limit));
        if (estimate > limit) return rich_request(pcm, true);
        SYS_RUN(pcm_read8(pcm, 0x4070, &limit));
        if (estimate > limit) return PCM_OK;
        return rich_request(pcm, false);
    }
reset_age:
    SYS_RUN(pcm_write8(pcm, 0x084c, 0));
    return rich_request(pcm, false);
}

/* D3B0..D471. Air rate is sampled once for the gain and the second surface
 * coordinate. The AFR correction is a signed byte about 128. */
PcmStatus pcm_catalyst_estimate(Pcm *pcm)
{
    if (pcm == NULL || pcm->calibration == NULL) return PCM_BAD_CONFIGURATION;
    if (!(pcm->calibration->mode_f & 0x10u) || pcm->scheduler.phase != 5 ||
        !pcm->runtime.spark_running) return PCM_OK;
    uint8_t throttle = pcm->reference.throttle, limit, age;
    SYS_RUN(pcm_read8(pcm, 0x4074, &limit));
    if (throttle <= limit) {
        SYS_RUN(pcm_write8(pcm, 0x7e, 0));
    } else {
        uint8_t rpm = pcm->reference.rpm_coordinate;
        SYS_RUN(pcm_read8(pcm, 0x4075, &limit));
        if (rpm < limit) {
            SYS_RUN(pcm_read8(pcm, 0x7e, &age));
            if (age != 255u) SYS_RUN(pcm_write8(pcm, 0x7e, (uint8_t)(age + 1u)));
        }
        SYS_RUN(pcm_read8(pcm, 0x7e, &age));
        SYS_RUN(pcm_read8(pcm, 0x4076, &limit));
        if (age >= limit) return PCM_OK;
    }
    uint8_t air = pcm->iac.runtime_high, gain, base, reaction;
    SYS_RUN(sys_curve16(pcm, air, 0x4077, &gain));
    SYS_RUN(pcm_write8(pcm, 0x7c, gain));
    SYS_RUN(egr_surface(pcm, (uint8_t)(pcm->reference.rpm_coordinate >> 1), air, 0x408f, &base));
    SYS_RUN(pcm_write8(pcm, 0x7b, base));
    uint8_t afr = pcm->fuel.commanded_afr;
    if (afr > 155u) afr = 155;
    uint8_t coordinate = afr > 107u ? (uint8_t)((afr - 107u) * 2u) : 0;
    SYS_RUN(sys_curve16(pcm, coordinate, 0x4088, &reaction));
    SYS_RUN(pcm_write8(pcm, 0x7d, reaction));
    SYS_RUN(pcm_read8(pcm, 0x7b, &base));
    int target = (int)base + reaction - 128;
    SYS_RUN(pcm_write8(pcm, 0x7a, target < 0 ? 0 : target > 255 ? 255 : (uint8_t)target));
    uint8_t target_byte;
    uint16_t old;
    SYS_RUN(pcm_read8(pcm, 0x7a, &target_byte));
    SYS_RUN(pcm_read8(pcm, 0x7c, &gain));
    SYS_RUN(pcm_read16(pcm, 0x78, &old));
    SYS_RUN(pcm_write16(pcm, 0x78, pcm_lag8(target_byte, old, gain)));
    return catalyst_request(pcm);
}
