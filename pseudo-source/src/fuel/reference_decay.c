#include "hardware.h"
#include "reference_math.h"
/* 7650..7696. The second ASLA's carry alone selects the FF coordinate. */
PcmStatus pcm_reference_decay(Pcm *pcm)
{
    PcmReference *state = &pcm->reference;
    const PcmReferenceCalibration *cal = &pcm->calibration->reference;
    if (!state->enrichment) return PCM_OK;
    if (state->enrichment_age != 255) ++state->enrichment_age;
    uint8_t first = pcm_lookup16(state->coolant, cal->decay_temperature);
    uint8_t coordinate = state->event_age & 0x40u ? 255 : (uint8_t)(state->event_age << 2);
    uint8_t second = pcm_lookup16(coordinate, cal->decay_event);
    if (((uint16_t)first * second >> 8) >= state->enrichment_age) return PCM_OK;
    ++state->decay_count; /* Byte wrap is intentional. */
    if (state->decay_count >= cal->decay_interval) {
        state->decay_count = 0;
        state->enrichment = state->enrichment < state->enrichment_decrement ? 0 :
                            (uint8_t)(state->enrichment - state->enrichment_decrement);
    }
    return PCM_OK;
}
