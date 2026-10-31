#include "spark.h"
#include "reference_math.h"
/* CAB4..CAD4: default zero, strict coolant gate, fault and PE qualification. */
PcmStatus pcm_spark_pe(Pcm *pcm)
{
    if (pcm->calibration == NULL || pcm->calibration->spark == NULL) return PCM_BAD_CONFIGURATION;
    uint8_t result = 0;
    if (pcm->reference.coolant > pcm->calibration->knock.minimum_coolant &&
        !pcm->knock.sensor_fault && pcm->runtime.power_enrichment) {
        uint8_t lookup = pcm_lookup16(pcm->reference.rpm_coordinate, pcm->calibration->spark->pe_curve);
        result = (uint8_t)(((uint16_t)lookup * pcm->spark.pe_fraction + 128u) >> 8);
    }
    pcm->spark.pe_advance = result;
    return PCM_OK;
}
