#include "spark.h"
#include "control.h"
#include "hardware.h"
#include "reference_math.h"
#define RUN(call) do { PcmStatus result = (call); if (result != PCM_OK) return result; } while (0)
/* A4EC..A580 and A59B..A5E4, with the A581 qualifier and timeout split out.
 * The bool distinguishes the normal A5E5 continuation from an AC51 tail exit. */
PcmStatus pcm_spark_admit(Pcm *pcm, bool *normal)
{
    if (normal == NULL) return PCM_BAD_CONFIGURATION;
    *normal = false;
    if (pcm->calibration == NULL || pcm->calibration->spark == NULL) return PCM_BAD_CONFIGURATION;
    const PcmSparkCalibration *cal = pcm->calibration->spark;
    if (pcm->reference.pending) {
        pcm->reference.pending = false;
        pcm->reference.consumed = true;
        pcm->spark.reference_age = 0;
        uint16_t old = pcm->spark.adaptive_period;
        uint16_t decayed = (uint16_t)(old - (old >> 3) - 1u);
        pcm->spark.adaptive_period = decayed & 0x8000u ? 0u : decayed;
        pcm->spark.missing_reference_count = 0;
        if (pcm->runtime.spark_running) {
            if (!pcm->runtime.fuel_running) RUN(pcm_spark_fuel_admit(pcm));
            if (pcm->spark.startup_gain_enabled && !pcm->spark.startup_gain_complete) {
                uint16_t gain = pcm->spark.startup_recovery_gain;
                if (gain > 0xfef0u) pcm->spark.startup_gain_complete = true;
                else pcm->spark.startup_recovery_gain = pcm_lag8(255, gain, cal->startup_gain);
            }
        } else {
            if (!pcm->spark.first_reference) {
                pcm->spark.first_reference = true;
                return pcm_alternate_rpm(pcm);
            }
            if (!pcm->runtime.fuel_running) RUN(pcm_spark_fuel_admit(pcm));
            uint16_t period;
            RUN(pcm_read16(pcm, PCM_REFERENCE_PERIOD, &period));
            if (period >= cal->spark_run_period_limit) {
                pcm->spark.spark_run_count = 0;
                return pcm_alternate_rpm(pcm);
            }
            ++pcm->spark.spark_run_count;
            if (pcm->spark.spark_run_count < cal->spark_run_events) return pcm_alternate_rpm(pcm);
            pcm->runtime.spark_running = true;
            pcm->spark.spark_run_count = 0;
            pcm->spark.run_transition = true;
            pcm->spark.startup_gain_complete = false;
            pcm->spark.startup_recovery_gain = 0;
        }
    } else {
        uint16_t age = pcm->spark.reference_age;
        if (age < cal->no_reference_age_limit) {
            ++age;
            pcm->spark.reference_age = age;
        } else RUN(pcm_write8(pcm, PCM_REFERENCE_AGE, 0));
        if (age >= 0x00a0u) {
            RUN(pcm_mask_irq(pcm, true));
            if (cal->missing_reference_age_cap < pcm->reference.event_age)
                pcm->reference.event_age = cal->missing_reference_age_cap;
        }
        RUN(pcm_mask_irq(pcm, false)); /* Literal CLI even if SEI was skipped. */
        if (pcm->spark.missing_reference_count >= 0x17u) return pcm_spark_timeout(pcm);
        if (!pcm->runtime.spark_running) return pcm_alternate_rpm(pcm);
        ++pcm->spark.missing_reference_count;
    }
    *normal = true;
    return PCM_OK;
}
