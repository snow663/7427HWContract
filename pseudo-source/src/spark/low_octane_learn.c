#include "knock.h"
/* CE10..CE7B: full-phase06 admission and the two-observation activity latches. */
PcmStatus pcm_low_octane_learn(Pcm *pcm)
{
    if (pcm->calibration == NULL) return PCM_BAD_CONFIGURATION;
    if (pcm->scheduler.phase != 6u) return PCM_OK;
    const PcmKnockCalibration *cal = &pcm->calibration->knock;
    uint8_t activity = pcm->knock.activity;
    if (pcm->knock.sensor_fault) {
        activity = activity >= cal->learn_decrement ? (uint8_t)(activity - cal->learn_decrement) : 0;
    } else {
        if (pcm->reference.coolant <= cal->learn_min_coolant) goto disqualify;
        uint8_t load = pcm->spark.load_coordinate;
        if (load < cal->learn_min_load) goto disqualify;
        uint8_t previous = pcm->spark.previous_load;
        if (load >= previous && (uint8_t)(load - previous) > cal->learn_load_change_limit) goto disqualify;
        uint8_t retard = pcm->knock.retard;
        if (retard <= cal->learn_low_retard) {
            if (pcm->knock.learning_low)
                activity = activity >= cal->learn_decrement ? (uint8_t)(activity - cal->learn_decrement) : 0;
            else { pcm->knock.learning_low = true;pcm->knock.learning_high = false; }
        } else if (retard <= cal->learn_high_retard) goto disqualify;
        else {
            if (pcm->knock.learning_high) {
                uint16_t sum = (uint16_t)activity + cal->learn_increment;
                activity = sum > 255u ? 255u : (uint8_t)sum;
            } else { pcm->knock.learning_high = true;pcm->knock.learning_low = false; }
        }
    }
    pcm->knock.activity = activity;
    pcm->knock.scaled_activity = (uint8_t)(((uint16_t)cal->learn_scale * activity + 128u) >> 8);
    return PCM_OK;
disqualify:
    pcm->knock.learning_high = false;
    pcm->knock.learning_low = false;
    return PCM_OK;
}
