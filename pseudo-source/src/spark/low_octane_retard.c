#include "knock.h"
#include "reference_math.h"
/* A77A..A791: two successive rounded byte products, not one combined product.
 * Sample0841 before the load lookup, then sample020A after the first product. */
PcmStatus pcm_low_octane_retard(Pcm *pcm)
{
    if (pcm->calibration == NULL) return PCM_BAD_CONFIGURATION;
    uint8_t rpm_factor = pcm->knock.octane_rpm_factor;
    uint8_t load_factor = pcm_lookup16(pcm->spark.load_coordinate, pcm->calibration->knock.octane_load);
    uint8_t first = (uint8_t)(((uint16_t)rpm_factor * load_factor + 128u) >> 8);
    pcm->knock.adaptive_retard = (uint8_t)(((uint16_t)first * pcm->knock.scaled_activity + 128u) >> 8);
    return PCM_OK;
}
