#include "hardware.h"
#define RUN(call) do { PcmStatus result = (call); if (result != PCM_OK) return result; } while (0)
static uint16_t doubled(uint16_t value) { return value & 0x8000u ? 0xffffu : (uint16_t)(value * 2u); }
/* 7696..7765, after the independent additional-AFR decay. */
PcmStatus pcm_reference_run(Pcm *pcm)
{
    PcmReference *state = &pcm->reference;
    const PcmReferenceCalibration *cal = &pcm->calibration->reference;
    RUN(pcm_reference_decay(pcm));
    if (!(cal->mode_c & 0x08u) || state->bank_fault) return pcm_reference_common(pcm);
    if (!state->packet_updated) {
        if (!state->split_latch) goto dispatch;
        state->split_latch = false;
        state->running_packet = doubled(state->running_packet);
        goto sum;
    }
    ++state->split_count;
    if (state->split_count >= 3) {
        RUN(pcm_write8(pcm, PCM_TFLG1, 1));
        if (state->running_packet < cal->running_packet_minimum) {
            if (state->split_count == 4) state->split_count = 0;
            return pcm_reference_common(pcm);
        }
        if (state->split_count == 4) state->split_latch = true;
        goto sum;
    }
    if (state->running_packet < cal->running_packet_minimum) goto dispatch;
    if (state->split_count == 1) state->split_latch = true;
    goto reset_counts;
sum:
    {
        uint16_t pulse = (uint16_t)(state->running_packet + state->additive_offset);
        state->timer_pulse = pulse & 0x8000u ? 0x7fff : pulse;
    }
reset_counts:
    state->packet_updated = false;
    state->split_clear = 0;
    state->split_count = 0;
dispatch:
    if (!(cal->mode_b & 0x20u)) state->bank_latch = true;
    uint8_t flags;
    RUN(pcm_read8(pcm, PCM_TFLG1, &flags));
    bool bank_b;
    if (flags & 1u) {
        RUN(pcm_write8(pcm, PCM_TFLG1, 1));
        state->bank_guard_count = 0;
        bank_b = !(cal->mode_b & 0x20u);
    } else {
        RUN(pcm_reference_bank_guard(pcm));
        bank_b = (cal->mode_b & 0x20u) != 0;
    }
    for (;;) {
        RUN(pcm_reference_timer_arm(pcm, bank_b));
        if (state->bank_latch) break;
        state->bank_latch = true;
        state->timer_delay = 0;
        bank_b = !bank_b;
    }
    return pcm_reference_common(pcm);
}
