#include "resident_input_private_1.h"

/* B2B2..B2C8. The first word is sampled even when the forward table
 * supersedes it. ASLB truncates the doubled index to eight bits. */
PcmStatus pcm_resident_gear_ratio(Pcm *pcm, uint16_t *ratio)
{
    uint8_t range, gear, fault;
    SYS_RUN(pcm_read16(pcm, 0x5b43, ratio));
    SYS_RUN(pcm_read8(pcm, 0xa2, &range));
    if (range & 0x20u) return PCM_OK;
    SYS_RUN(pcm_read8(pcm, 0xd9, &gear));
    SYS_RUN(pcm_read8(pcm, 0x98, &fault));
    if (fault & 4u) gear = 1;
    return pcm_read16(pcm, (uint16_t)(0x5b49u + (uint8_t)(gear << 1)), ratio);
}
