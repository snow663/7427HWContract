#ifndef PCM_TEMPERATURE_INTERNAL_H
#define PCM_TEMPERATURE_INTERNAL_H
#include "board_io.h"
#include "../system/system_internal.h"

static inline uint8_t temperature_convert(Pcm *pcm, uint8_t sample, uint8_t range_bit)
{
    bool first = pcm->runtime.first_conversion || (pcm->io.auxiliary_output & range_bit);
    return pcm->calibration->air->coolant_table[first ? 0 : 1][sample];
}

static inline void temperature_range(Pcm *pcm, uint8_t value, uint8_t range_bit)
{
    if (value > 120u) pcm->io.auxiliary_output &= (uint8_t)~range_bit;
    else if (value <= 106u) pcm->io.auxiliary_output |= range_bit;
}

/* C900/C9C3. Each fault enable is sampled independently. Stop checking
 * as soon as the first enabled/live fault selects the fallback. */
static inline PcmStatus temperature_filter(Pcm *pcm, uint8_t sample, uint16_t enables,
                                           uint16_t faults, uint16_t fallback, uint16_t gain,
                                           uint16_t destination, uint8_t *high)
{
    for (uint8_t bit = 0x40; bit >= 0x20; bit >>= 1) {
        uint8_t flags;
        SYS_RUN(pcm_read8(pcm, enables, &flags));
        if (flags & bit) {
            SYS_RUN(pcm_read8(pcm, faults, &flags));
            if (flags & bit) {
                SYS_RUN(pcm_read8(pcm, fallback, &sample));
                break;
            }
        }
    }
    uint16_t old, result;
    SYS_RUN(pcm_read16(pcm, destination, &old));
    SYS_RUN(sys_lag16(pcm, (uint16_t)(256u * sample + 128u), old, gain, &result));
    SYS_RUN(pcm_write16(pcm, destination, result));
    *high = (uint8_t)(result >> 8);
    return PCM_OK;
}
#endif
