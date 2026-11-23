#include "control.h"
#include "hardware.h"
#include "../system/system_internal.h"

/* D320..D365. The old timer controls admission. INC reads its operand again. */
static PcmStatus update_multiplier(Pcm *pcm)
{
    uint8_t vacuum = pcm->spark.vacuum, limit, age, multiplier, step;
    SYS_RUN(pcm_read8(pcm, 0x4024, &limit));
    if (vacuum <= limit && !pcm->fuel.map_acceleration && !pcm->fuel.tps_acceleration) {
        SYS_RUN(pcm_read8(pcm, 0x01d8, &age));
        SYS_RUN(pcm_read8(pcm, 0x4025, &limit));
        if (age < limit) {
            SYS_RUN(pcm_read8(pcm, 0x01d8, &age));
            return pcm_write8(pcm, 0x01d8, (uint8_t)(age + 1u));
        }
        SYS_RUN(pcm_read8(pcm, 0x01d7, &multiplier));
        uint8_t integrator = pcm->fuel.integrator;
        SYS_RUN(pcm_read8(pcm, 0x4026, &limit));
        if (integrator >= limit) {
            SYS_RUN(pcm_read8(pcm, 0x4029, &step));
            unsigned sum = (unsigned)multiplier + step;
            SYS_RUN(pcm_write8(pcm, 0x01d7, sum > 255u ? 255 : (uint8_t)sum));
        } else {
            SYS_RUN(pcm_read8(pcm, 0x4027, &limit));
            if (integrator < limit) {
                SYS_RUN(pcm_read8(pcm, 0x402a, &step));
                SYS_RUN(pcm_write8(pcm, 0x01d7, multiplier < step ? 0 : (uint8_t)(multiplier - step)));
            }
        }
    }
    return pcm_write8(pcm, 0x01d8, 0);
}

static PcmStatus purge_duty(Pcm *pcm)
{
    uint8_t curve, scale, duty;
    if (!(pcm->io.coolant_context & 0x80u)) {
        SYS_RUN(sys_curve16(pcm, pcm->iac.runtime_high, 0x4047, &curve));
        SYS_RUN(pcm_read8(pcm, 0x4028, &scale));
        uint16_t biased = (uint16_t)((unsigned)curve * scale + 64u);
        return pcm_write8(pcm, 0x01d6, biased > 0x7fffu ? 255 : (uint8_t)(biased >> 7));
    }
    SYS_RUN(update_multiplier(pcm));
    SYS_RUN(sys_curve16(pcm, pcm->iac.runtime_high, 0x4036, &curve));
    SYS_RUN(pcm_read8(pcm, 0x01d7, &scale));
    SYS_RUN(pcm_write8(pcm, 0x01d6, (uint8_t)(((unsigned)curve * scale + 128u) >> 8)));
    SYS_RUN(sys_curve16(pcm, pcm->iac.runtime_high, 0x4047, &curve));
    SYS_RUN(pcm_read8(pcm, 0x01d6, &duty));
    if (curve > duty) return pcm_write8(pcm, 0x01d6, curve);
    return PCM_OK;
}

/* D2B2..D3AF. The hot-start path precedes DFCO and normal hysteresis. */
PcmStatus pcm_canister_purge(Pcm *pcm)
{
    if (pcm == NULL) return PCM_BAD_CONFIGURATION;
    if (pcm->scheduler.phase & 0x10u) return PCM_OK;
    uint8_t flags, sample, limit, duty;
    if (pcm->calibration == NULL) return PCM_BAD_CONFIGURATION;
    if (!(pcm->calibration->reference.mode_c & 0x80u)) goto disable;
    sample = pcm->reference.coolant;
    SYS_RUN(pcm_read8(pcm, 0x402c, &limit));
    if (sample > limit) {
        uint16_t elapsed = pcm->scheduler.run_counter, maximum;
        SYS_RUN(pcm_read16(pcm, 0x402d, &maximum));
        if (elapsed <= maximum) {
            SYS_RUN(pcm_write8(pcm, 0x01d6, 255));
            goto publish;
        }
    }
    if (pcm->runtime.deceleration_fuel_cut) goto disable;
    sample = pcm->reference.coolant;
    SYS_RUN(pcm_read8(pcm, 0x402b, &limit));
    if (sample <= limit) goto disable;
    SYS_RUN(pcm_read8(pcm, 0x41, &flags));
    uint16_t row = flags & 0x80u ? 0x4033 : 0x4030;
    sample = pcm->spark.vehicle_speed_high;
    SYS_RUN(pcm_read8(pcm, row, &limit));
    if (sample < limit) goto disable;
    sample = pcm->reference.throttle;
    SYS_RUN(pcm_read8(pcm, (uint16_t)(row + 2u), &limit));
    if (sample < limit) goto disable;
    sample = (uint8_t)(pcm->spark.density >> 8);
    SYS_RUN(pcm_read8(pcm, (uint16_t)(row + 1u), &limit));
    if (sample < limit) goto disable;
    SYS_RUN(pcm_read8(pcm, (uint16_t)(0x4058u + pcm->iac.blm_cell_index), &flags));
    if (!flags) goto disable;
    SYS_RUN(purge_duty(pcm));
    goto publish;
disable:
    SYS_RUN(pcm_write8(pcm, 0x01d6, 0));
    SYS_RUN(pcm_write8(pcm, 0x01d8, 0));
    sample = pcm->spark.vehicle_speed_high;
    SYS_RUN(pcm_read8(pcm, 0x402f, &limit));
    if (sample < limit) SYS_RUN(pcm_write8(pcm, 0x01d7, 0));
publish:
    SYS_RUN(pcm_update8(pcm, 0x41, 0x80, 0));
    SYS_RUN(pcm_read8(pcm, 0x01d6, &duty));
    if (duty != 0) return pcm_update8(pcm, 0x41, 0, 0x80);
    return PCM_OK;
}
