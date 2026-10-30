#include "hardware.h"
#define RUN(call) do { PcmStatus result = (call); if (result != PCM_OK) return result; } while (0)

/* FFF2 ->74EA; implemented prefix ends at751B. Target entry/RTI must preserve
 * the real frame with I masked. Neither this prefix nor its stock continuation
 * opens ordinary nesting. The body continues in pcm_reference_event(). */
PcmStatus pcm_reference_prefix(Pcm *pcm)
{
    uint16_t timer;
    uint8_t board;
    if (pcm->runtime.factory_mode) return PCM_FACTORY_BOUNDARY;
    if (pcm->calibration == NULL) return PCM_BAD_CONFIGURATION;
    RUN(pcm_read16(pcm, PCM_TCNT, &timer));
    /* Stock byte offset is (RAM0062 >> 1) & FE: 64 words, no interpolation. */
    uint8_t index = (uint8_t)(pcm->reference.rpm_coordinate >> 2);
    RUN(pcm_write16(pcm, PCM_TOC1,
                    (uint16_t)(timer + pcm->calibration->reference_compare_counts[index])));
    RUN(pcm_read8(pcm, PCM_REFERENCE_STROBE, &board));
    RUN(pcm_write8(pcm, PCM_REFERENCE_STROBE, (uint8_t)(board & 0xbfu)));
    /* The second read is part of the BSET transaction, not the first sample. */
    RUN(pcm_read8(pcm, PCM_REFERENCE_STROBE, &board));
    RUN(pcm_write8(pcm, PCM_REFERENCE_STROBE, (uint8_t)(board | 0x40u)));
    if (!pcm->reference.latch_inhibited) pcm->reference.pending = true;
    RUN(pcm_write8(pcm, PCM_REFERENCE_AGE, 0xff));
    return PCM_OK;
}
