#include "control.h"
#include "hardware.h"
#include "reference_math.h"
#include "../system/system_internal.h"

static PcmStatus air_decision(Pcm *pcm)
{
    uint8_t age = 0, flags, limit;
    bool active = false;
    if (pcm->runtime.engine_service) {
        SYS_RUN(pcm_read8(pcm, 0x038f, &flags));
        if (flags & 2u) {
            SYS_RUN(pcm_read8(pcm, 0x0390, &flags));
            active = (flags & 2u) != 0;
            goto publish;
        }
    }
    uint8_t coolant = pcm->reference.coolant;
    SYS_RUN(pcm_read8(pcm, 0x4e8c, &limit));
    if (coolant < limit) goto publish;
    SYS_RUN(pcm_read8(pcm, 0x71, &flags));
    if (flags & 1u) goto publish;
    if (pcm->runtime.power_enrichment) {
        SYS_RUN(pcm_read8(pcm, 0x0279, &age));
        SYS_RUN(pcm_read8(pcm, 0x4e8d, &limit));
        if (age > limit) goto publish;
        ++age;
    } else {
        uint8_t rpm = pcm->spark.rpm_low_coordinate;
        SYS_RUN(pcm_read8(pcm, 0x4e8a, &limit));
        if (rpm > limit) goto publish;
        uint8_t map = pcm->spark.map_filtered;
        SYS_RUN(pcm_read8(pcm, 0x4e8b, &limit));
        if (map < limit || (!pcm->fuel.idle_afr_ready && (pcm->io.coolant_context & 0x80u))) goto publish;
    }
    active = true;
publish:
    SYS_RUN(pcm_update8(pcm, 0x46, 4, active ? 4 : 0));
    return pcm_write8(pcm, 0x0279, age);
}

static PcmStatus stopped_outputs(Pcm *pcm, bool diagnostic)
{
    SYS_RUN(pcm_write8(pcm, 0x01d6, diagnostic ? 255 : 0));
    SYS_RUN(pcm_update8(pcm, 0x46, 4, diagnostic ? 4 : 0));
    if (!diagnostic) {
        SYS_RUN(pcm_update8(pcm, 0x53, 4, 0));
        pcm->transmission.shift_lamp = false;
    }
    SYS_RUN(pcm_update8(pcm, 0x41, 0x10, diagnostic ? 0x10 : 0));
    pcm->io.ac_mirror = diagnostic;
    return pcm_update8(pcm, 0x52, 8, diagnostic ? 8 : 0);
}

static PcmStatus shared_command(Pcm *pcm)
{
    uint8_t flags, value;
    uint16_t command = 0x7000;
    SYS_RUN(pcm_read8(pcm, 0x0393, &flags));
    if (flags & 0x38u) {
        SYS_RUN(pcm_read8(pcm, 0x0394, &value));
        command |= (uint16_t)((uint16_t)value << 4);
    } else if (pcm->calibration->mode_f & 1u) {
        uint8_t rpm = pcm->reference.rpm_coordinate;
        SYS_RUN(pcm_read8(pcm, 0x50dc, &value));
        if (rpm >= value) command = 0x7fff;
    } else {
        SYS_RUN(pcm_read8(pcm, 0x52, &flags));
        if ((flags & 8u) || ((pcm->calibration->mode_f & 4u) && !pcm->io.ac_mirror)) command = 0x7fff;
    }
    return pcm_write16(pcm, 0x3fd4, command);
}

/* CCC1..CDF6. The service purge byte overrides the output only.
 * Repeated high battery takes the stopped-output clear path even while running. */
PcmStatus pcm_air_shared_outputs(Pcm *pcm)
{
    if (pcm == NULL || pcm->calibration == NULL) return PCM_BAD_CONFIGURATION;
    uint16_t old;
    uint8_t gain, flags, duty;
    SYS_RUN(pcm_read16(pcm, 0x01d0, &old));
    SYS_RUN(pcm_read8(pcm, 0x4e89, &gain));
    SYS_RUN(pcm_write16(pcm, 0x01d0, pcm_lag8(pcm->fuel.raw_oxygen, old, gain)));
    if (pcm->calibration->reference.mode_b & 2u) SYS_RUN(air_decision(pcm));

    bool forced_off = false;
    if (pcm->spark.battery_sample >= 171u) {
        SYS_RUN(pcm_read8(pcm, 0x51, &flags));
        forced_off = (flags & 0x10u) != 0;
        if (!forced_off) SYS_RUN(pcm_update8(pcm, 0x51, 0, 0x10));
    } else SYS_RUN(pcm_update8(pcm, 0x51, 0x10, 0));
    if (forced_off) SYS_RUN(stopped_outputs(pcm, false));
    else if (!pcm->runtime.spark_running) {
        SYS_RUN(pcm_read8(pcm, 0x71, &flags));
        SYS_RUN(stopped_outputs(pcm, (flags & 0x80u) != 0));
    }
    SYS_RUN(pcm_read8(pcm, 0x46, &flags));
    SYS_RUN(pcm_write16(pcm, 0x3fda, flags & 4u ? 0xdfff : 0xd000));
    uint16_t source = 0x01d6;
    if (pcm->runtime.engine_service) {
        SYS_RUN(pcm_read8(pcm, 0x0393, &flags));
        if (flags & 4u) source = 0x0394;
    }
    SYS_RUN(pcm_read8(pcm, source, &duty));
    SYS_RUN(pcm_write16(pcm, 0x3fd6, (uint16_t)(0xb000u | ((uint16_t)duty << 3))));
    SYS_RUN(shared_command(pcm));
    if (pcm->calibration->reference.mode_e & 4u)
        SYS_RUN(pcm_write16(pcm, 0x306c, pcm->transmission.shift_lamp ? 0x1fff : 0x1f00));
    if (pcm->calibration->mode_f & 0x40u)
        SYS_RUN(pcm_write16(pcm, PCM_TCC_COMMAND, pcm->transmission.range_context & 0x20u ? 0x7fff : 0x7f00));
    return PCM_OK;
}
