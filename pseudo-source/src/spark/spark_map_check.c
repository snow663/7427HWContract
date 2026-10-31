#include "spark.h"
/* A4B3..A4EB: clear both indications first; old count>limit latches the fault. */
PcmStatus pcm_spark_map_check(Pcm *pcm)
{
    if (pcm->calibration == NULL || pcm->calibration->spark == NULL) return PCM_BAD_CONFIGURATION;
    const PcmSparkCalibration *cal = pcm->calibration->spark;
    pcm->spark.map_fault = false;
    pcm->spark.load_status &= (uint8_t)~0x08u;
    if ((pcm->spark.load_status & 0x04u) || pcm->reference.map_sample >= cal->map_sample_minimum)
        pcm->spark.map_fault_count = 0;
    else if (pcm->spark.map_fault_count > cal->map_count_limit) {
        pcm->spark.map_fault = true;
        pcm->spark.load_status |= 0x08u;
    } else if (pcm->spark.rpm_low_coordinate < cal->map_rpm_minimum || pcm->reference.throttle > cal->map_throttle_limit)
        ++pcm->spark.map_fault_count;
    else pcm->spark.map_fault_count = 0;
    return PCM_OK;
}
