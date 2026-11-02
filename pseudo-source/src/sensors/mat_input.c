#include "board_io.h"
#include "hardware.h"
#include "reference_math.h"
#define RUN(call) do { PcmStatus result = (call); if (result != PCM_OK) return result; } while (0)
/* DBFB..DC88. CLI precedes the ADC read; diagnostic counters use old values. */
PcmStatus pcm_mat_input(Pcm *pcm)
{
    RUN(pcm_mask_irq(pcm, true));
    RUN(pcm_adc_mux(pcm, 4));
    RUN(pcm_adc_convert(pcm, 1));
    RUN(pcm_mask_irq(pcm, false));
    uint8_t sample;
    RUN(pcm_read8(pcm, PCM_ADR4, &sample));
    pcm->io.mat_raw = (uint8_t)~sample;
    if (pcm->calibration == NULL || pcm->calibration->air == NULL) return PCM_BAD_CONFIGURATION;
    const PcmAirCalibration *cal = pcm->calibration->air;
    if (pcm->scheduler.run_counter > cal->mat_runtime_limit) {
        uint8_t speed = pcm->spark.vehicle_speed_high;
        if (cal->mat_options & 0x40u) {
            pcm->io.mat_low_fault = false;
            if (pcm->io.mat_raw < cal->mat_low_threshold) {
                if (pcm->io.mat_low_count > cal->mat_low_delay) pcm->io.mat_low_fault = true;
                else if (speed <= cal->mat_speed_limit) ++pcm->io.mat_low_count;
                else pcm->io.mat_low_count = 0;
            } else pcm->io.mat_low_count = 0;
        } else pcm->io.mat_low_count = 0;
        if (cal->mat_options & 0x10u) {
            pcm->io.mat_high_fault = false;
            if (pcm->io.mat_raw >= cal->mat_high_threshold) {
                if (pcm->io.mat_high_count > cal->mat_high_delay) pcm->io.mat_high_fault = true;
                else if (speed > cal->mat_speed_limit) ++pcm->io.mat_high_count;
                else pcm->io.mat_high_count = 0;
            } else pcm->io.mat_high_count = 0;
        } else pcm->io.mat_high_count = 0;
    }
    uint8_t value = pcm_lookup16(pcm->io.mat_raw, cal->mat_curve);
    pcm->io.mat_display = value;
    pcm->spark.mat_sample = pcm->io.mat_low_fault || pcm->io.mat_high_fault ? cal->mat_default : value;
    return PCM_OK;
}
