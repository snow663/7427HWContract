#include "temperature_internal.h"

/* C9C0..C9F6. A fault substitution affects the filter input. */
PcmStatus pcm_coolant_filter(Pcm *pcm)
{
    if (pcm == NULL) return PCM_BAD_CONFIGURATION;
    uint8_t temperature, limit;
    SYS_RUN(temperature_filter(pcm, pcm->io.coolant_conversion, 0x5b2b, 0x16,
                               0x5b17, 0x5d0c, 0xa9, &temperature));
    SYS_RUN(pcm_read8(pcm, 0x5d04, &limit));
    if (temperature > limit) return pcm_update8(pcm, 0x87, 0, 0x04);
    SYS_RUN(pcm_read8(pcm, 0x5d05, &limit));
    if (temperature < limit) return pcm_update8(pcm, 0x87, 0x04, 0);
    return PCM_OK;
}
