#include "spark.h"
#include "reference_math.h"
/* AB44..AB88: sign from bit15, byte magnitude, wrapping startup gain,
 * optional180F, capped latency and rounded period product. saved becomes local. */
PcmStatus pcm_spark_convert(Pcm *pcm, uint16_t *saved)
{
    if (saved == NULL || pcm->calibration == NULL || pcm->calibration->spark == NULL)
        return PCM_BAD_CONFIGURATION;
    const PcmSparkCalibration *cal = pcm->calibration->spark;
    pcm->spark.command_negative = false;
    uint16_t command = pcm->spark.command;
    uint8_t magnitude = (uint8_t)command;
    if (command & 0x8000u) {
        pcm->spark.command_negative = true;
        magnitude = (uint8_t)(0u - magnitude);
    }
    if (!pcm->spark.startup_gain_complete) {
        uint8_t factor = (uint8_t)(pcm->spark.startup_recovery_gain >> 8);
        if (pcm->spark.startup_recovery_gain & 0x80u) ++factor;
        magnitude = (uint8_t)(((uint16_t)magnitude * factor >> 8) + 1u);
    }
    PcmStatus result = pcm_spark_output_extension(pcm, &magnitude);
    if (result != PCM_OK) return result;
    uint8_t latency;
    result = pcm_lookup_capped(pcm->reference.rpm_coordinate, &cal->output_latency, &latency);
    if (result != PCM_OK) return result;
    pcm->spark.output_latency = latency;
    uint16_t product = pcm_gain_word(pcm->spark.period_basis, magnitude);
    uint16_t signed_product = pcm->spark.command_negative ? product : (uint16_t)(0u - product);
    *saved = (uint16_t)(signed_product - pcm->spark.output_latency);
    return PCM_OK;
}
