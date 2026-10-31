#include "spark.h"
/* AADC..AB19: transmission precedence, then recovery/TPS or normal floor. */
PcmStatus pcm_spark_lower_limit(Pcm *pcm)
{
    if (pcm->calibration == NULL || pcm->calibration->spark == NULL) return PCM_BAD_CONFIGURATION;
    const PcmSparkCalibration *cal = pcm->calibration->spark;
    uint16_t bound;
    if (pcm->spark.transmission_retard != 0) {
        bound = cal->lower_transmission;
        if (pcm->spark.transmission_status & 0x08u) goto compare;
        if (pcm->spark.transmission_status & 0x17u) { bound = cal->lower_transmission_state;goto compare; }
    }
    if (pcm->spark.recovery_active && pcm->reference.throttle <= pcm->calibration->reference.throttle_limit)
        bound = cal->lower_recovery;
    else bound = cal->lower_normal;
compare:
    if ((uint16_t)(bound ^ 0x8000u) >= (uint16_t)(pcm->spark.command ^ 0x8000u)) pcm->spark.command = bound;
    return PCM_OK;
}
