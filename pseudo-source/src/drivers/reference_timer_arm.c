#include "hardware.h"
#define RUN(call) do { PcmStatus result = (call); if (result != PCM_OK) return result; } while (0)
/* 77C7..77F6 /77F7..7826. Preserve the N-only modular comparison. */
PcmStatus pcm_reference_timer_arm(Pcm *pcm, bool bank_b)
{
    uint16_t timer, previous;
    uint16_t delay = pcm->reference.timer_delay;
    if (delay < 6) delay = 6;
    RUN(pcm_read16(pcm, PCM_TCNT, &timer));
    uint16_t candidate = (uint16_t)(timer + delay);
    if (bank_b) pcm->reference.compare_b = candidate;
    else pcm->reference.compare_a = candidate;
    uint8_t flag = bank_b ? 0x10u : 0x08u, port;
    uint16_t compare = bank_b ? PCM_TOC4 : PCM_TOC5;
    RUN(pcm_write8(pcm, PCM_TFLG1, flag));
    RUN(pcm_update8(pcm, PCM_TMSK1, 0, flag));
    RUN(pcm_read8(pcm, PCM_PORTA, &port));
    if (port & flag) {
        RUN(pcm_read16(pcm, compare, &previous));
        if (!((uint16_t)(candidate - previous) & 0x8000u)) return PCM_OK;
    }
    RUN(pcm_update8(pcm, PCM_TCTL1, 0, bank_b ? 0x0cu : 0x03u));
    return pcm_write16(pcm, compare, candidate);
}
