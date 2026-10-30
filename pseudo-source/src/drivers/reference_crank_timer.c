#include "hardware.h"
#include "reference_math.h"
#define RUN(call) do { PcmStatus result = (call); if (result != PCM_OK) return result; } while (0)
static uint16_t doubled(uint16_t value) { return value & 0x8000u ? 0xffffu : (uint16_t)(value * 2u); }
/* 7587..7628, entered after storing the limited additive packet at0250. */
PcmStatus pcm_reference_crank_timer(Pcm *pcm)
{
    PcmReference *state = &pcm->reference;
    uint8_t flags;
    RUN(pcm_read8(pcm, PCM_TFLG1, &flags));
    bool bank_b = (flags & 1u) != 0;
    if (!bank_b) {
        if (state->crank_references == 1) state->crank_timer_latch = true;
        else if (state->crank_timer_latch) {
            state->timer_pulse = doubled(pcm_gain_word(state->timer_pulse, pcm->calibration->reference.crank_timer_gain));
            if (state->event_age) --state->event_age;
        }
        RUN(pcm_update8(pcm, PCM_TCTL1, 0, 0x03));
        RUN(pcm_update8(pcm, PCM_CFORC, 0, 0x08));
        RUN(pcm_reference_bank_guard(pcm));
    } else {
        RUN(pcm_write8(pcm, PCM_TFLG1, 1));
        state->bank_guard_count = 0;
        RUN(pcm_update8(pcm, PCM_TCTL1, 0, 0x0c));
        RUN(pcm_update8(pcm, PCM_CFORC, 0, 0x10));
        state->crank_timer_latch = false;
    }
    uint16_t timer;
    RUN(pcm_read16(pcm, PCM_TCNT, &timer));
    uint16_t candidate = (uint16_t)(doubled(state->timer_pulse) + timer);
    if (bank_b) state->extended_b = candidate;
    else state->extended_a = candidate;
    RUN(pcm_update8(pcm, PCM_TCTL1, bank_b ? 0x04 : 0x01, 0));
    RUN(pcm_read16(pcm, PCM_TCNT, &timer));
    uint16_t near = (uint16_t)(timer + 2u);
    uint16_t selected = (uint16_t)(near - candidate) & 0x8000u ? candidate : near;
    return pcm_write16(pcm, bank_b ? PCM_TOC4 : PCM_TOC5, selected);
}
