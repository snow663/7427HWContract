#include "fuel.h"
#include "mixture_internal.h"
#include "reference_math.h"
/* 8A92..8C37. All counters use full phase equality and old-count comparisons. */
PcmStatus pcm_fuel_pe(Pcm *pcm)
{
    MIX_CAL();
    if (pcm->spark.vehicle_speed_high < cal->pe_permission_speed && pcm->reference.throttle <= cal->pe_permission_throttle) {
        pcm->fuel.pe_permission = true;
        pcm->fuel.pe_permission_count = 0;
    } else if (pcm->fuel.pe_permission_count < cal->pe_permission_delay) {
        ++pcm->fuel.pe_permission_count;
        pcm->fuel.pe_permission = true;
    }
    uint8_t value;
    MIX_RUN(mix_h1(pcm->reference.rpm_coordinate, 32, &cal->pe_upper, &value));
    pcm->fuel.pe_upper_throttle = value;
    MIX_RUN(mix_h1(pcm->reference.rpm_coordinate, 32, &cal->pe_exit, &value));
    pcm->fuel.pe_exit_step = value;
    MIX_RUN(mix_h1(pcm->reference.rpm_coordinate, 32, &cal->pe_entry, &value));
    pcm->fuel.pe_entry_throttle = value;
    uint8_t threshold = pcm->runtime.power_enrichment ? mix_sub(value, cal->pe_hysteresis) : value;
    if (pcm->reference.throttle <= threshold) goto ordinary_exit;
    if (pcm->fuel.pe_full_gain) goto full_gain;
    if (mix_sub(pcm->spark.rpm_high, pcm->io.map_previous_rpm) > cal->pe_rpm_delta) {
        pcm->fuel.pe_full_gain = true;
        goto full_gain;
    }
    if (pcm->reference.coolant > cal->pe_coolant[1] || pcm->reference.coolant <= cal->pe_coolant[0] || pcm->reference.rpm_coordinate >= cal->pe_rpm) goto full_gain;
    if (pcm->reference.throttle >= pcm->fuel.pe_previous_throttle && pcm->reference.throttle - pcm->fuel.pe_previous_throttle >= pcm->io.pe_throttle_threshold) {
        pcm->fuel.pe_full_gain = true;
        goto full_gain;
    }
    if (pcm->reference.rpm_coordinate < pcm->io.pe_rpm_threshold && !pcm->runtime.power_enrichment) goto ordinary_exit;
    if (!pcm->fuel.pe_permission) goto vehicle_exit;
    if (pcm->fuel.pe_gain_count < cal->pe_gain_delay) ++pcm->fuel.pe_gain_count;
    else {
        pcm->spark.pe_fraction = mix_byte((unsigned)pcm->spark.pe_fraction + cal->pe_gain_step);
        pcm->fuel.pe_gain_count = 0;
    }
    goto target;
full_gain:
    pcm->spark.pe_fraction = 255;
    pcm->fuel.pe_gain_count = 0;
target:
    pcm->runtime.power_enrichment = true;
    value = pcm_lookup16(pcm->reference.rpm_coordinate, cal->pe_target);
    if (pcm->fuel.pe_target_count <= cal->pe_time) {
        if (pcm->scheduler.phase == 7) ++pcm->fuel.pe_target_count;
        if (pcm->reference.rpm_coordinate < cal->pe_rpm && pcm->reference.coolant <= cal->pe_warm_coolant && pcm->reference.coolant > cal->pe_coolant[0] && pcm->reference.throttle <= pcm->fuel.pe_upper_throttle) {
            uint16_t numerator = (uint16_t)((uint16_t)mix_sub(pcm->reference.throttle, pcm->fuel.pe_entry_throttle) << 8);
            uint16_t denominator = (uint16_t)((uint16_t)mix_sub(pcm->fuel.pe_upper_throttle, pcm->fuel.pe_entry_throttle) << 8);
            uint8_t ratio = (uint8_t)(mix_fraction(numerator, denominator) >> 8);
            value = mix_byte((unsigned)value + mix_sub(cal->pe_part_throttle, mix_round(ratio, cal->pe_part_throttle)));
        }
    }
    if (pcm->reference.coolant <= cal->pe_cold_coolant && pcm->reference.rpm_coordinate < cal->pe_cold_rpm && pcm->spark.vehicle_speed_high < cal->pe_cold_speed) value = mix_sub(value, cal->pe_cold_subtract);
    if (pcm->fuel.commanded_afr > value) pcm->fuel.commanded_afr = (uint8_t)(pcm->fuel.commanded_afr - mix_round(pcm->spark.pe_fraction, (uint8_t)(pcm->fuel.commanded_afr - value)));
    return PCM_OK;
vehicle_exit:
    if (pcm->fuel.pe_vehicle_change < cal->pe_vehicle_change) goto ordinary_exit;
    if (pcm->fuel.pe_exit_count == 0) {
        pcm->fuel.pe_permission = true;
        pcm->fuel.pe_gain_count = 0;
        goto target;
    }
    value = pcm->reference.throttle <= pcm->fuel.pe_upper_throttle ? (uint8_t)(pcm->fuel.pe_exit_count - 1u) : mix_sub(pcm->fuel.pe_exit_count, pcm->fuel.pe_exit_step);
    goto timed_exit;
ordinary_exit:
    if (pcm->fuel.pe_exit_count >= cal->pe_exit_delay) {
        pcm->spark.pe_fraction = 0;
        pcm->fuel.pe_target_count = 0;
        goto clear;
    }
    value = (uint8_t)(pcm->fuel.pe_exit_count + 1u);
timed_exit:
    if (pcm->scheduler.phase == 0x17u) pcm->fuel.pe_exit_count = value;
clear:
    pcm->fuel.pe_permission = false;
    pcm->runtime.power_enrichment = false;
    pcm->fuel.pe_full_gain = false;
    return PCM_OK;
}
