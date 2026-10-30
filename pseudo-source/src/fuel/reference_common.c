#include "hardware.h"
#define RUN(call) do { PcmStatus result = (call); if (result != PCM_OK) return result; } while (0)
/* 7765..77C6. F479's intermediate006A store precedes the final returned value. */
PcmStatus pcm_reference_common(Pcm *pcm)
{
    PcmReference *state = &pcm->reference;
    const PcmReferenceCalibration *cal = &pcm->calibration->reference;
    uint16_t status;
    RUN(pcm_read16(pcm, PCM_REFERENCE_STATUS, &status));
    bool requested = ((status >> 8) & 0x40u) || state->extra_request;
    state->extra_request = false;
    if (!requested) return PCM_OK;
    if (state->load_coordinate >= cal->load_minimum && state->throttle <= cal->throttle_limit) {
        uint16_t target = state->load_filtered, old = state->load_event;
        uint16_t difference = (uint16_t)(target - old);
        int32_t high = difference >> 8;
        if (target < old) high -= 256;
        uint16_t intermediate = (uint16_t)((int32_t)old + high * cal->load_event_gain);
        state->load_event = intermediate;
        state->load_event = (uint16_t)(intermediate + (((difference & 255u) * cal->load_event_gain + 128u) >> 8));
    } else state->load_event = state->load_filtered;
    if (!(cal->mode_b & 0x01u)) return PCM_OK;
    if ((cal->mode_c & 0x08u) && !state->bank_fault) return PCM_OK;
    if (state->packet_updated) {
        if (!state->extra_guard) {
            state->extra_guard = true;
            return PCM_OK;
        }
        if (state->running_packet > cal->running_packet_minimum) state->packet_updated = false;
    }
    state->extra_guard = false;
    RUN(pcm_reference_timer_arm(pcm, false));
    return pcm_reference_timer_arm(pcm, true);
}
