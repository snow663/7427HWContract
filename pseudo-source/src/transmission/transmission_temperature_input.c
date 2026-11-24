#include "control.h"
#include "../sensors/temperature_internal.h"

/* C8D6..C8FC. This channel shares the first-conversion flag with coolant.
 * It changes auxiliary range bit 1 and leaves first_conversion for C96A. */
PcmStatus pcm_transmission_temperature_input(Pcm *pcm)
{
    if (pcm == NULL || pcm->calibration == NULL || pcm->calibration->air == NULL) return PCM_BAD_CONFIGURATION;
    uint8_t sample = temperature_convert(pcm, pcm->io.auxiliary_reference, 2u);
    temperature_range(pcm, sample, 2u);
    return pcm_write8(pcm, 0xb4, sample);
}
