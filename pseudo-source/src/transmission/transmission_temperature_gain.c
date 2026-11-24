#include "gear_internal.h"
#include "reference_math.h"

/* D92E..D968. Select using the live gear even for a downshift threshold
 * whose speed-table column used gear - 1. D94B returns the gain in A. */
PcmStatus pcm_transmission_temperature_gain(Pcm *pcm, uint16_t table, uint16_t input, uint16_t *result)
{
    if (pcm == NULL || result == NULL) return PCM_BAD_CONFIGURATION;
    uint8_t gear, selector;
    uint16_t pointer;
    bool valid;
    SYS_RUN(pcm_read8(pcm, 0x00d9, &gear));
    SYS_RUN(pcm_read8(pcm, 0x0082, &selector));
    SYS_RUN(pcm_transmission_descriptor(pcm, table, selector, gear, &pointer, &valid));
    if (!valid) {
        *result = input;
        return PCM_OK;
    }
    uint8_t knot, pressure;
    SYS_RUN(pcm_read8(pcm, pointer, &knot));
    SYS_RUN(pcm_read8(pcm, 0x00ac, &pressure));
    int32_t offset = (int32_t)knot - 128;
    uint16_t gain_word = (uint16_t)(32768L + (2L * pressure - 256L) * offset);
    uint16_t scaled = pcm_gain_word(input, (uint8_t)(gain_word >> 8));
    *result = scaled > 0x7fffu ? UINT16_MAX : (uint16_t)(2u * scaled);
    return PCM_OK;
}
