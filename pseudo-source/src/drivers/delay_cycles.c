#include "hardware.h"
/* A target binding must wait at least the requested nominal E cycles.
 * Returning success without that delay is a test-fixture behavior only. */
PcmStatus pcm_delay_cycles(Pcm *pcm, uint16_t cycles)
{
    if (pcm->platform == NULL || pcm->platform->delay_cycles == NULL) return PCM_NO_HARDWARE;
    return pcm->platform->delay_cycles(pcm->platform->context, cycles);
}
