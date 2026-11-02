#include "control.h"
/* 91A3..920D. RAM000A is committed before SEI. B's local copy supplies the
 * merge even if the mask callback changes000A;004C is sampled after SEI.
 * CLI opens the mask literally rather than restoring its incoming value. */
PcmStatus pcm_iac_step(Pcm *pcm)
{
    uint8_t mode = pcm->iac.step_control;
    uint8_t battery = pcm->spark.battery_sample;
    bool admitted = false;
    if (battery > 169u) mode &= (uint8_t)~0x10u;
    else if (pcm->reference.latch_inhibited) admitted = true;
    else {
        if (pcm->calibration == NULL || pcm->calibration->iac == NULL) return PCM_BAD_CONFIGURATION;
        admitted = battery > pcm->calibration->iac->step_battery_minimum;
    }
    pcm->iac.low_battery = !admitted;
    if (admitted) {
        mode |= 0x10u;
        uint8_t position = pcm->iac.position, target = pcm->iac.target;
        if (position == target) mode &= (uint8_t)~1u;
        else if (!(pcm->iac.state_flags & 1u) || (pcm->scheduler.phase & 3u) != 3u) {
            bool decreasing = position > target;
            if (decreasing) mode |= 1u;else mode &= (uint8_t)~1u;
            if (decreasing == ((pcm->iac.step_control & 1u) != 0)) {
                pcm->iac.position = decreasing ? (uint8_t)(position - 1u) : (uint8_t)(position + 1u);
                uint8_t ring = pcm->iac.step_control & 0x0cu;
                bool aligned = ring == 0 || ring == 0x0cu;
                mode ^= aligned == decreasing ? 8u : 4u;
            }
        }
    }
    pcm->iac.step_control = mode;
    PcmStatus result = pcm_mask_irq(pcm, true);
    if (result != PCM_OK) return result;
    pcm->transmission.output_shadow = (uint8_t)((pcm->transmission.output_shadow & 0xe3u) + (mode & 0x1cu));
    return pcm_mask_irq(pcm, false);
}
