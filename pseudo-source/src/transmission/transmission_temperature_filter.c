#include "control.h"
#include "../sensors/temperature_internal.h"

/* C947..C969. FDIV saturates when the divisor is zero or the numerator
 * reaches it. Re-read both breakpoints and A9 on the intermediate path. */
static PcmStatus publish_cold_weight(Pcm *pcm, uint8_t coolant)
{
    uint8_t lower, upper, weight = 0;
    SYS_RUN(pcm_read8(pcm, 0x5d36, &lower));
    if (coolant <= lower) {
        weight = 255;
    } else {
        SYS_RUN(pcm_read8(pcm, 0x5d37, &upper));
        if (coolant < upper) {
            SYS_RUN(pcm_read8(pcm, 0x5d37, &upper));
            SYS_RUN(pcm_read8(pcm, 0x5d36, &lower));
            uint8_t span = (uint8_t)(upper - lower);
            SYS_RUN(pcm_read8(pcm, 0xa9, &coolant));
            SYS_RUN(pcm_read8(pcm, 0x5d36, &lower));
            uint8_t distance = (uint8_t)(coolant - lower);
            if (distance < span) weight = (uint8_t)~((256u * distance) / span);
        }
    }
    return pcm_write8(pcm, 0xab, weight);
}

/* C8FD..C969. The hot flag uses B5. The other flag and cold weight use A9. */
PcmStatus pcm_transmission_temperature_filter(Pcm *pcm)
{
    if (pcm == NULL) return PCM_BAD_CONFIGURATION;
    uint8_t sample, temperature, limit, flags, coolant;
    SYS_RUN(pcm_read8(pcm, 0xb4, &sample));
    SYS_RUN(temperature_filter(pcm, sample, 0x5b30, 0x1b, 0x5b6a, 0x5d0b, 0xb5, &temperature));
    SYS_RUN(pcm_read8(pcm, 0x6abb, &limit));
    SYS_RUN(pcm_read8(pcm, 0x87, &flags));
    if (!(flags & 2u)) SYS_RUN(pcm_read8(pcm, 0x6aba, &limit));
    SYS_RUN(pcm_update8(pcm, 0x87, 2u, 0));
    if (temperature >= limit) SYS_RUN(pcm_update8(pcm, 0x87, 0, 2u));
    SYS_RUN(pcm_read8(pcm, 0xa9, &coolant));
    SYS_RUN(pcm_read8(pcm, 0x5d34, &limit));
    if (coolant < limit) SYS_RUN(pcm_update8(pcm, 0x87, 0, 1u));
    SYS_RUN(pcm_read8(pcm, 0x5d35, &limit));
    if (coolant > limit) SYS_RUN(pcm_update8(pcm, 0x87, 1u, 0));
    return publish_cold_weight(pcm, coolant);
}
