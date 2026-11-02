#include "fuel.h"
#include "delivery_internal.h"
#include "hardware.h"
/*8058..810B. true enters821D; false continues810C with cut state cleared. */
PcmStatus pcm_fuel_cut_gate(Pcm *pcm, bool *reduce)
{
    if (reduce == NULL) return PCM_BAD_CONFIGURATION;
    *reduce = false;DL_CAL();
    if (!(pcm->runtime.primary_faults & 0x10u)) {
        bool evaluate = true;
        if (!(pcm->calibration->mode_f & 0x80u)) {
            if (pcm->iac.park_neutral) pcm->fuel.qualification_count = cal->qualification_reload;
            else if (pcm->fuel.qualification_count == 0) evaluate = false;
            else --pcm->fuel.qualification_count;
        }
        if (evaluate && (pcm->io.vss_raw>>8) <= cal->qualification_speed && pcm->reference.throttle > cal->qualification_throttle) {
            uint8_t threshold=cal->qualification_rpm[pcm->fuel.qualification_latch ? 1 : 0];
            if (pcm->spark.rpm_low_coordinate > threshold) { pcm->fuel.qualification_latch=true;*reduce=true;return PCM_OK; }
            pcm->fuel.qualification_latch=false;
        }
    }
    if (!((pcm->calibration->mode_f & 1u) && !(pcm->spark.load_status & 0x34u))) {
        unsigned index=pcm->fuel.cut_active ? 1u : 0u;
        unsigned fault=((pcm->runtime.primary_faults & 0x10u) || (pcm->transmission.inhibit_flags & 3u)) ? 2u : 0u;
        if (pcm->reference.rpm_coordinate > cal->cut_rpm[index+fault]) goto cut;
        if (pcm->spark.vehicle_speed_high > cal->cut_speed[index] && pcm->reference.rpm_coordinate > cal->cut_minimum_rpm) {
            if (pcm->fuel.cut_count >= cal->cut_delay) goto cut;
            ++pcm->fuel.cut_count;
            pcm->fuel.cut_active=false;
            return PCM_OK;
        }
    }
    pcm->fuel.cut_count=0;pcm->fuel.cut_active=false;return PCM_OK;
cut:
    pcm->fuel.cut_active=true;pcm->fuel.corrected_pulse=0;*reduce=true;return PCM_OK;
}
