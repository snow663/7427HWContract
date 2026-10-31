#include "spark.h"
#include "hardware.h"
/* A581..A59A: independent fuel-running qualifier; increment wraps as a byte. */
PcmStatus pcm_spark_fuel_admit(Pcm *pcm)
{
    if (pcm->calibration == NULL || pcm->calibration->spark == NULL) return PCM_BAD_CONFIGURATION;
    const PcmSparkCalibration *cal = pcm->calibration->spark;
    uint16_t period;
    PcmStatus result = pcm_read16(pcm, PCM_REFERENCE_PERIOD, &period);
    if (result != PCM_OK) return result;
    uint8_t count = 0;
    if (period < cal->fuel_run_period_limit) {
        count = (uint8_t)(pcm->spark.fuel_run_count + 1u);
        if (count >= cal->fuel_run_events) { pcm->runtime.fuel_running = true;count = 0; }
    }
    pcm->spark.fuel_run_count = count;
    return PCM_OK;
}
