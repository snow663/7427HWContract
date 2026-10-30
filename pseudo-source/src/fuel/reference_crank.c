#include "hardware.h"
#include "reference_math.h"
#define RUN(call) do { PcmStatus result = (call); if (result != PCM_OK) return result; } while (0)
/* 7535..764F. A rejected event exits without the later event-age update. */
PcmStatus pcm_reference_crank(Pcm *pcm)
{
    PcmReference *state = &pcm->reference;
    const PcmReferenceCalibration *cal = &pcm->calibration->reference;
    state->load_event = state->load_filtered;
    if (state->latch_inhibited) return pcm_write8(pcm, PCM_TFLG1, 1);
    if (state->crank_references != 255) ++state->crank_references;
    if (state->crank_references <= pcm_lookup16(state->coolant, cal->crank_skip))
        return pcm_write8(pcm, PCM_TFLG1, 1);
    if (cal->mode_c & 0x04u) {
        state->delivered_pulse = pcm_crank_event_gain(pcm);
        if (!(cal->mode_b & 0x10u)) RUN(pcm_fuel_async(pcm, state->delivered_pulse));
        else if (state->bank_fault) {
            state->delivered_pulse >>= 1;
            RUN(pcm_fuel_async(pcm, state->delivered_pulse));
        } else {
            uint16_t pulse = (uint16_t)(state->delivered_pulse + state->additive_offset);
            state->timer_pulse = pulse & 0x8000u ? 0x7fff : pulse;
            RUN(pcm_reference_crank_timer(pcm));
        }
    }
    uint8_t age = (uint8_t)(state->event_age + 1u);
    if (!age) age = 0xf0;
    state->event_age = age;
    if (state->battery <= cal->battery_limit && age > cal->crank_age_cap)
        state->event_age = cal->crank_age_cap;
    return PCM_OK;
}
