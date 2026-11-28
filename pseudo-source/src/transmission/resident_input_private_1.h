#ifndef PCM_RESIDENT_INPUT_PRIVATE_1
#define PCM_RESIDENT_INPUT_PRIVATE_1
#include "resident_transmission.h"
#include "reference_math.h"
#include "../system/system_internal.h"
static inline int16_t signed_byte(uint8_t x)
{
    return x < 128u ? (int16_t)x : (int16_t)x - 256;
}

/* The factory samples suppression, enable and live status in that order.
 * Preserve the separate reads and stop at the first nonzero witness. */
static inline PcmStatus mask_test(Pcm *pcm, uint16_t suppress, uint16_t enable,
                           uint16_t live, uint8_t bits, bool *active)
{
    uint8_t a, b, c;
    SYS_RUN(pcm_read8(pcm, suppress, &a));
    SYS_RUN(pcm_read8(pcm, enable, &b));
    SYS_RUN(pcm_read8(pcm, live, &c));
    *active = (((uint8_t)~a & b & c & bits) != 0);
    return PCM_OK;
}

/* E60B..E62C and E6F5..E716 share the exact mask-scan form. */
static inline PcmStatus paired_fault(Pcm *pcm, uint8_t first, uint8_t second, uint8_t bit)
{
    bool active;
    SYS_RUN(mask_test(pcm, 0x5b35, 0x5b2c, 0x17, first, &active));
    if (!active) SYS_RUN(mask_test(pcm, 0x5b3a, 0x5b31, 0x1c, second, &active));
    return pcm_update8(pcm, 0x98, bit, active ? bit : 0);
}

#endif
