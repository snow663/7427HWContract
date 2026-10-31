#include "spark.h"
#include "reference_math.h"
/* A764..A779. Disabled altitude retains the old term; it does not reset bias. */
PcmStatus pcm_spark_altitude(Pcm *pcm)
{
    if (pcm->calibration == NULL || pcm->calibration->spark == NULL) return PCM_BAD_CONFIGURATION;
    if (!(pcm->calibration->mode_d & 4u)) return PCM_OK;
    uint8_t row = pcm->spark.barometric_pressure;
    uint8_t column = pcm->spark.vacuum, result;
    PcmStatus status = pcm_lookup2d(row, column, &pcm->calibration->spark->altitude, &result);
    if (status == PCM_OK) pcm->spark.altitude_advance = result;
    return status;
}
