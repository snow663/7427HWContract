#include "control.h"
/* CB15..CC34. Diagnostic publication precedes the optional AC body.
 * Literal mask assignments and completed failure prefixes are observable. */
PcmStatus pcm_ac_switch_inputs(Pcm *pcm)
{
    PcmStatus result=pcm_mask_irq(pcm,true);
    if (result!=PCM_OK) return result;
    pcm->runtime.diagnostic_switch=false;pcm->io.diagnostic_warm=false;
    uint8_t sample=pcm->io.diagnostic_sample;
    if (sample<40u) pcm->runtime.diagnostic_switch=true;
    else if (sample<100u && pcm->runtime.factory_mode) pcm->io.diagnostic_warm=true;
    result=pcm_mask_irq(pcm,false);
    if (result!=PCM_OK) return result;
    if (pcm->calibration==NULL) return PCM_BAD_CONFIGURATION;
    if (!(pcm->calibration->mode_f&4u)) return PCM_OK;
    if (pcm->calibration->ac==NULL) return PCM_BAD_CONFIGURATION;
    const PcmAcCalibration *cal=pcm->calibration->ac;
    if (pcm->scheduler.run_counter<cal->runtime_minimum || !(pcm->iac.input_shadow&1u)) {
        pcm->io.ac_entry=cal->entry_delay;goto reload_exit;
    }
    if (pcm->io.ac_entry) { --pcm->io.ac_entry;goto rpm_guard; }
    if (cal->throttle_limit[pcm->io.ac_mirror?1:0]>=pcm->reference.throttle) {
        pcm->io.ac_throttle_count=0;goto context_check;
    }
    if (pcm->io.ac_throttle_count>cal->throttle_count_limit) goto context_check;
    ++pcm->io.ac_throttle_count;goto rpm_guard;
context_check:
    if (pcm->iac.context&0x10u) goto clear_mirror;
    if (cal->coolant_limit[pcm->io.ac_mirror?1:0]<pcm->reference.coolant) goto reload_exit;
    if (!(pcm->runtime.primary_faults&0x10u) &&
        cal->speed_limit[pcm->io.ac_mirror?0:1]>pcm->spark.vehicle_speed_high) {
        uint8_t throttle=cal->throttle_release[pcm->io.ac_mirror?1:0];
        if (pcm->io.ac_mirror) pcm->io.ac_throttle_delay=cal->throttle_delay;
        if (throttle<pcm->reference.throttle && pcm->io.ac_throttle_delay) {
            --pcm->io.ac_throttle_delay;goto reload_exit;
        }
    }
    if (cal->rpm_limit[pcm->io.ac_mirror?0:1]>=pcm->reference.rpm_coordinate)
        pcm->io.ac_rpm_count=0;
    else {
        if (pcm->io.ac_rpm_count>=cal->rpm_count_limit) goto rpm_guard;
        uint8_t next=(uint8_t)(pcm->io.ac_rpm_count+1u);
        if (next) pcm->io.ac_rpm_count=next;
    }
    if (pcm->io.ac_rpm_inhibit) goto rpm_guard;
    pcm->iac.ac_request=true;
    if (pcm->io.ac_exit) --pcm->io.ac_exit;
    else pcm->io.ac_mirror=true;
    return PCM_OK;
reload_exit:
    pcm->io.ac_exit=cal->exit_delay;
rpm_guard:
    if (pcm->runtime.spark_running) {
        if (pcm->reference.rpm_coordinate>cal->running_rpm_limit) {
            pcm->io.ac_rpm_inhibit=true;pcm->io.ac_release_count=0;pcm->io.ac_exit=cal->exit_delay;
        } else if (pcm->io.ac_release_count>=cal->rpm_release_delay) pcm->io.ac_rpm_inhibit=false;
        else {
            uint8_t next=(uint8_t)(pcm->io.ac_release_count+1u);
            if (next) pcm->io.ac_release_count=next;
        }
    }
    pcm->iac.ac_request=false;
clear_mirror:
    pcm->io.ac_mirror=false;return PCM_OK;
}
