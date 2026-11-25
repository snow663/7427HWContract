#include "control.h"
#include "../system/system_internal.h"

/* $C413..$C444 and $C44B..$C47F. In the second window the upper
 * comparison samples coolant again. The two MUL/ADCA rounds are separate. */
static PcmStatus apply_window(Pcm *pcm, uint16_t lower, uint16_t gain_address,
                              bool resample)
{
    uint8_t coolant, limit, gain;
    SYS_RUN(pcm_read8(pcm, 0x00a9, &coolant));
    SYS_RUN(pcm_read8(pcm, lower, &limit));
    bool above = coolant >= limit;
    if (above) {
        if (resample) SYS_RUN(pcm_read8(pcm, 0x00a9, &coolant));
        SYS_RUN(pcm_read8(pcm, lower + 1u, &limit));
        if (coolant <= limit) return PCM_OK;
    }
    SYS_RUN(pcm_read8(pcm, gain_address, &gain));
    SYS_RUN(pcm_read8(pcm, above ? lower + 1u : lower, &limit));
    if (above) {
        coolant = (uint8_t)~coolant;
        limit = (uint8_t)~limit;
    }
    /* High byte of FDIV; a changed denominator may saturate. */
    uint8_t fraction = coolant >= limit ? 255u : (uint8_t)(((uint16_t)coolant << 8) / limit);
    uint16_t scaled = ((uint16_t)fraction * gain + 128u) >> 8;
    pcm->spark.transmission_retard = (uint8_t)((scaled * pcm->spark.transmission_retard + 128u) >> 8);
    return PCM_OK;
}

/* $C40A..$C482, final callee of $C4E5. $015A also feeds the engine spark sum. */
PcmStatus pcm_transmission_spark_coolant(Pcm *pcm)
{
    uint8_t override;
    SYS_RUN(pcm_read8(pcm, 0x0119, &override));
    if (override != 0) {
        pcm->spark.transmission_retard = override;
        return PCM_OK;
    }
    if (pcm->spark.transmission_status & 0x08u)
        SYS_RUN(apply_window(pcm, 0x70b2, 0x70b7, false));
    if (pcm->spark.transmission_status & 0x17u)
        SYS_RUN(apply_window(pcm, 0x70b4, 0x70b6, true));
    return PCM_OK;
}
