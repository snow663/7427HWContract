#include "fuel.h"
#include "hardware.h"
/* 8613..863C. Raw00A7, not the separately acquired0055 battery sample. */
PcmStatus pcm_fuel_battery_state(Pcm *pcm)
{
    uint8_t sample = pcm->spark.battery_sample;
    if (sample < 90) {
        if (sample < 40) {
            pcm->reference.latch_inhibited = true;
            pcm->reference.sample_map = false;
        }
        return PCM_OK;
    }
    if (pcm->reference.latch_inhibited) {
        uint16_t baseline;
        PcmStatus result = pcm_read16(pcm, PCM_EST_COUNTER, &baseline);
        if (result != PCM_OK) return result;
        pcm->spark.bypass_baseline = baseline;
    }
    pcm->reference.latch_inhibited = false;
    if (pcm->calibration == NULL) return PCM_BAD_CONFIGURATION;
    if (pcm->calibration->reference.mode_c & 1u) pcm->reference.sample_map = true;
    return PCM_OK;
}
