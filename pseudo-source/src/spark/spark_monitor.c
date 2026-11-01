#include "spark.h"
#include "hardware.h"
#define RUN(call) do { PcmStatus result = (call); if (result != PCM_OK) return result; } while (0)
/* ABCB..AC50, followed by shared ACA0/ACA3 exits. Counter/feedback words are
 * distinct hardware samples. F3ED is an RTS, not an extra device transaction. */
PcmStatus pcm_spark_monitor(Pcm *pcm)
{
    if (pcm->spark.first_reference) {
        if (!pcm->reference.consumed) goto cleanup;
        if (pcm->calibration == NULL || pcm->calibration->spark == NULL) return PCM_BAD_CONFIGURATION;
        const PcmSparkCalibration *cal = pcm->calibration->spark;
        uint16_t sample;
        RUN(pcm_read16(pcm, PCM_EST_COUNTER, &sample));
        if (!(cal->bypass_options & 0x20u)) goto enable;
        if (pcm->spark.startup_gain_enabled) goto handoff;
        if (pcm->spark.bypass_fault_latched) goto fault;
        uint16_t delta = (uint16_t)(sample - pcm->spark.bypass_baseline);
        if ((delta >> 8) != 0 || (uint8_t)delta > cal->bypass_delta_limit) {
            uint8_t count = pcm->spark.bypass_count;
            if (count > cal->bypass_count_limit) {
                pcm->spark.bypass_fault_latched = true;
                goto fault;
            }
            pcm->spark.bypass_count = (uint8_t)(count + 1u);
            pcm->spark.bypass_qualified = false;
        } else {
            if (pcm->spark.bypass_qualified) goto enable;
            pcm->spark.bypass_qualified = true;
        }
        pcm->spark.bypass_baseline = sample;
        goto cleanup;
enable:
        pcm->spark.startup_gain_enabled = true;
        pcm->spark.bypass_count = 0;
        pcm->spark.bypass_baseline = sample;
handoff:
        pcm->spark.first_reference = false;
        uint16_t feedback;
        RUN(pcm_read16(pcm, PCM_EST_FEEDBACK, &feedback));
        RUN(pcm_write16(pcm, PCM_EST_HANDOFF, feedback));
    }
    pcm->spark.output_request = true;
    if (pcm->spark.bypass_supervision && !pcm->runtime.output_override) {
        pcm->spark.est_fault = true;
        pcm->spark.output_request = false;
    } else if (pcm->runtime.engine_service && pcm->spark.service_bypass) {
        pcm->runtime.output_override = true;
        pcm->spark.output_request = false;
    }
cleanup:
    pcm->reference.consumed = false;
    return PCM_OK;
fault:
    pcm->spark.est_fault = true;
    goto cleanup;
}
