#include "iac.h"
#include "hardware.h"
#include "reference_math.h"
/* 989C..99C4, including the9250 switch sample. The expiry-call timer route
 * skips its BLM adder; only a subsequent old-count>=limit call adds it. */
PcmStatus pcm_iac_desired(Pcm *pcm)
{
    if (pcm->iac.transfer_flags & 0x40u) return PCM_OK;
    if (pcm->calibration == NULL || pcm->calibration->iac == NULL) return PCM_BAD_CONFIGURATION;
    const PcmIacCalibration *cal = pcm->calibration->iac;
    uint8_t temperature = pcm->iac.coolant_index;
    if (temperature > 160u) temperature = (uint8_t)(2u * (temperature - 160u) + 160u);
    unsigned ac = (pcm->iac.context & 1u) != 0;
    unsigned drive = (pcm->iac.context & 2u) != 0;
    uint8_t requested = pcm_lookup16(temperature, cal->rpm_curve[2u * drive + ac]);
    uint8_t battery = pcm->spark.battery_sample;
    if (battery < cal->battery_threshold) {
        uint8_t add = (uint8_t)(((uint16_t)(cal->battery_threshold - battery) * cal->battery_gain) >> 8);
        if (add > cal->battery_limit) add = cal->battery_limit;
        requested = (uint8_t)(requested + add);
    }
    uint8_t rough = (uint8_t)(((uint16_t)(pcm->iac.rpm_error_filtered >> 8) * cal->rough_gain) >> 8);
    if (rough > cal->rough_limit) rough = cal->rough_limit;
    requested = (uint8_t)(requested + rough);
    if (pcm->iac.blm_cell_index < 16u || pcm->iac.blm_value >= cal->blm_limit ||
        pcm->reference.coolant <= cal->blm_coolant_minimum) pcm->iac.blm_count = 0;
    else if (pcm->iac.blm_count < cal->blm_count_limit) {
        if ((pcm->scheduler.phase & 0xf0u) == 0) ++pcm->iac.blm_count;
    } else {
        drive = (pcm->iac.context & 2u) != 0;
        ac = (pcm->iac.context & 1u) != 0;
        requested = (uint8_t)(requested + cal->blm_adder[2u * drive + ac]);
    }
    uint8_t startup = pcm->iac.startup_rpm_adder;
    if (startup != 0 && !(pcm->iac.context & 2u))
        startup = (uint8_t)(((uint16_t)(uint8_t)(2u * startup) * cal->startup_rpm_gain + 128u) >> 8);
    requested = (uint8_t)(requested + startup);
    uint8_t old = pcm->iac.slewed_base;
    if (requested < old) requested = (uint8_t)(old - 1u);
    pcm->iac.slewed_base = requested;
    if (cal->options & 0x10u) {
        uint8_t threshold = cal->switch_threshold[(pcm->iac.context & 2u) != 0];
        if (requested >= threshold) {
            pcm->iac.switch_offset = 0;
            pcm->iac.switch_delay = cal->switch_up_delay;
            requested = pcm->iac.slewed_base;
        } else {
            uint8_t sample;
            PcmStatus result = pcm_read8(pcm, PCM_PORTD, &sample);
            if (result != PCM_OK) return result;
            if ((sample & 4u) && threshold <= pcm->spark.iac_desired_speed) requested = threshold;
            else {
                uint8_t offset = pcm->iac.switch_offset, delay;
                if (!(sample & 4u) && offset == 0) delay = cal->switch_down_delay;
                else {
                    delay = pcm->iac.switch_delay;
                    if (delay != 0) --delay;
                    else if (sample & 4u) { ++offset;delay = cal->switch_up_delay; }
                    else { --offset;delay = cal->switch_down_delay; }
                }
                pcm->iac.switch_offset = offset;
                requested = (uint8_t)(offset + pcm->iac.slewed_base);
                pcm->iac.switch_delay = delay;
            }
        }
    }
    pcm->spark.iac_desired_speed = requested;
    uint8_t factor = cal->stall_factor[pcm->iac.context & 3u];
    pcm->iac.stall_threshold = cal->options & 0x80u ? factor : (uint8_t)(((uint16_t)requested * factor) >> 8);
    return PCM_OK;
}
