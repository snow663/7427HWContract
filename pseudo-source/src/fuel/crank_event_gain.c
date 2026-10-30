#include "reference_math.h"
/* 7827..7859: event-count gain selection and saturated doubling. */
uint16_t pcm_crank_event_gain(const Pcm *pcm)
{
    const PcmReferenceCalibration *cal = &pcm->calibration->reference;
    uint8_t age = pcm->reference.event_age, gain;
    if (age > 23) gain = cal->crank_repeat[age & 7u];
    else if (pcm->scheduler.clear_after_run_count) gain = cal->crank_hot[age];
    else if (pcm->reference.coolant >= cal->coolant_gain_threshold) gain = cal->crank_warm[age];
    else gain = cal->crank_cold[age];
    uint16_t pulse = pcm_gain_word(pcm->reference.crank_seed, gain);
    return pulse & 0x8000u ? 0xffffu : (uint16_t)(pulse * 2u);
}
