#include "hardware.h"
/* Reference F3E4..F3EC. Physical purpose of 3066.7 remains unspecified. */
PcmStatus pcm_heartbeat_toggle(Pcm *pcm)
{
    uint8_t previous;
    PcmStatus result = pcm_read8(pcm, PCM_BOARD_HEARTBEAT, &previous);
    if (result != PCM_OK) return result;
    return pcm_write8(pcm, PCM_BOARD_HEARTBEAT, (uint8_t)(previous ^ 0x80u));
}
