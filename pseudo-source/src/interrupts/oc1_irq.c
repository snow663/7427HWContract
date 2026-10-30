#include "hardware.h"
/* FFE8 ->CE7C..CEBA. The target wrapper supplies the real frame, masked
 * entry and RTI. This body never opens ordinary nesting or changes TOC1. */
PcmStatus pcm_oc1_irq(Pcm *pcm)
{
    if (pcm->calibration == NULL) return PCM_BAD_CONFIGURATION;
    PcmStatus result = pcm_write8(pcm, PCM_TFLG1, 0x80);
    if (result != PCM_OK) return result;
    uint16_t sample;
    result = pcm_read16(pcm, PCM_KNOCK_COUNTER, &sample);
    if (result != PCM_OK) return result;
    uint16_t delta = (uint16_t)(sample - pcm->knock.sample_baseline);
    uint8_t clipped = delta > 255u ? 255u : (uint8_t)delta;
    /* Baseline advances even when the observation is rejected below. */
    pcm->knock.sample_baseline = sample;
    uint8_t index = (uint8_t)(pcm->reference.rpm_coordinate >> 2);
    uint8_t floor = pcm->calibration->knock.noise_floor[index];
    if (clipped <= floor) return PCM_OK;
    uint8_t excess = (uint8_t)(clipped - floor);
    /* The ROM samples 0062 again for this independently addressed table. */
    index = (uint8_t)(pcm->reference.rpm_coordinate >> 2);
    uint16_t biased = (uint16_t)excess + pcm->calibration->knock.observation_bias[index];
    if (biased > 255u) pcm->knock.observation_accumulator = 255;
    else {
        uint16_t accumulated = biased + pcm->knock.observation_accumulator;
        pcm->knock.observation_accumulator = accumulated > 255u ? 255u : (uint8_t)accumulated;
    }
    return PCM_OK;
}
