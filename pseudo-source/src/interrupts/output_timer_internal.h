#ifndef PCM_OUTPUT_TIMER_INTERNAL_H
#define PCM_OUTPUT_TIMER_INTERNAL_H
#include "hardware.h"

#define OUTPUT_RUN(call) do { PcmStatus result = (call); \
    if (result != PCM_OK) return result; } while (0)

/* The factory leaves differ only in bank addresses/masks. Their ordinary
 * interrupt entry is already masked. Native frame preservation and RTI are
 * wrapper responsibilities; these bodies neither enable IRQs nor use C SP.
 * Named RAM stays in the same owners used by the REF arm/crank producers. */
static inline PcmStatus output_timer_irq(Pcm *pcm, bool bank_b)
{
    if (pcm == NULL) return PCM_BAD_CONFIGURATION;
    uint8_t mask = bank_b ? 0x10u : 0x08u;
    uint8_t action = bank_b ? 0x04u : 0x01u;
    uint16_t compare = bank_b ? PCM_TOC4 : PCM_TOC5;
    volatile uint16_t *armed = bank_b ? &pcm->reference.compare_b :
                                      &pcm->reference.compare_a;
    volatile uint16_t *extended = bank_b ? &pcm->reference.extended_b :
                                         &pcm->reference.extended_a;
    volatile uint16_t *deadline;
    uint8_t port;

    /* Literal W1C acknowledgment precedes every read and other write. */
    OUTPUT_RUN(pcm_write8(pcm, PCM_TFLG1, mask));
    OUTPUT_RUN(pcm_read8(pcm, PCM_PORTA, &port));
    if (port & mask) {
        OUTPUT_RUN(pcm_update8(pcm, PCM_TMSK1, mask, 0));
        OUTPUT_RUN(pcm_update8(pcm, PCM_TCTL1, action, 0));
        bool consume = pcm->fuel.async_suppressed;
        uint32_t pulse = pcm->reference.timer_pulse;
        if (consume) pulse += pcm->fuel.acceleration_reservoir;
        /* ADDD carry and ASLD carry both saturate. Widen before addition;
         * unsigned int itself is only 16 bits on the intended HC11 target. */
        uint16_t width = pulse >= 0x8000UL ? 0xffffu : (uint16_t)(pulse * 2u);
        uint16_t previous;
        OUTPUT_RUN(pcm_read16(pcm, compare, &previous));
        *extended = (uint16_t)(width + previous); /* Timer offset wraps. */
        if (consume) {
            pcm->fuel.acceleration_reservoir = 0;
            pcm->fuel.async_suppressed = false;
        }
        deadline = extended;
    } else {
        OUTPUT_RUN(pcm_update8(pcm, PCM_TCTL1, 0, action));
        deadline = armed;
    }

    uint16_t timer;
    OUTPUT_RUN(pcm_read16(pcm, PCM_TCNT, &timer));
    uint16_t selected = (uint16_t)(timer + 2u);
    /* CPD/BPL uses N alone, not N xor V or an unsigned maximum. The
     * conditional volatile reload preserves the factory LDD after CPD. */
    if ((uint16_t)(selected - *deadline) & 0x8000u) selected = *deadline;
    return pcm_write16(pcm, compare, selected);
}

#undef OUTPUT_RUN
#endif
