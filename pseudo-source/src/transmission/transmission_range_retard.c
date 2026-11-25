#include "spark_internal.h"

/* $DA6F..$DAE1. A shift in progress retains its previous retard unless
 * the fault gate clears it first. Decay stores before decrementing $015E. */
PcmStatus pcm_transmission_range_retard(Pcm *pcm)
{
    uint8_t value = 0;
    if (pcm->transmission.inhibit_flags & 0x10u) goto publish;
    if (pcm->spark.transmission_status & 8u) return PCM_OK;
    if (pcm->spark.transmission_status & 1u) {
        SYS_RUN(transmission_retard_surface(pcm, 0x55f5, &value));
    } else if (pcm->spark.transmission_status & 2u) {
        SYS_RUN(pcm_read8(pcm, 0x55f3, &value));
    } else if (pcm->spark.transmission_status & 16u) {
        uint8_t limit, remaining;
        SYS_RUN(pcm_read8(pcm, 0x70d2, &limit));
        SYS_RUN(pcm_read8(pcm, 0x15e, &remaining));
        uint8_t fraction = remaining >= limit ? 255u : (uint8_t)(((uint16_t)remaining << 8) / limit);
        SYS_RUN(pcm_read8(pcm, 0x55f3, &value));
        pcm->spark.transmission_retard = (uint8_t)(((uint16_t)value * fraction) >> 8);
        SYS_RUN(pcm_read8(pcm, 0x15e, &remaining));
        SYS_RUN(pcm_write8(pcm, 0x15e, (uint8_t)(remaining - 1u)));
        if (pcm->spark.transmission_status & 4u) {
            uint8_t applied = pcm->spark.transmission_retard;
            SYS_RUN(pcm_read8(pcm, 0x55f4, &limit));
            if (applied <= limit) {
                SYS_RUN(pcm_read8(pcm, 0x55f4, &value));
                pcm->spark.transmission_retard = value;
                goto end_decay;
            }
        }
        SYS_RUN(pcm_read8(pcm, 0x15e, &remaining));
        if (remaining != 0) return PCM_OK;
end_decay:
        pcm->spark.transmission_status &= (uint8_t)~16u;
        return PCM_OK;
    } else if (pcm->spark.transmission_status & 4u) {
        SYS_RUN(pcm_read8(pcm, 0x55f4, &value));
    }
publish:
    pcm->spark.transmission_retard = value;
    return PCM_OK;
}
