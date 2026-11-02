#include "board_io.h"
#include "hardware.h"
#include "reference_math.h"
#define RUN(call) do { PcmStatus result = (call); if (result != PCM_OK) return result; } while (0)
/* C583..C667. Direct MAP admission precedes faults; retained BARO can skip filtering. */
PcmStatus pcm_baro_input(Pcm *pcm)
{
    if (pcm->calibration == NULL || pcm->calibration->air == NULL) return PCM_BAD_CONFIGURATION;
    const PcmAirCalibration *cal = pcm->calibration->air;
    uint8_t value;
    bool filter = true, use_default = false;
    if (cal->baro_options & 4u) {
        RUN(pcm_mask_irq(pcm, true));
        RUN(pcm_adc_mux(pcm, 5));
        RUN(pcm_adc_convert(pcm, 1));
        RUN(pcm_mask_irq(pcm, false));
        RUN(pcm_read8(pcm, PCM_ADR4, &value));
        pcm->io.barometric_sample = value;
        value = value > 244u ? 255u : (uint8_t)(value + 11u);
    } else if (pcm->reference.latch_inhibited || pcm->spark.map_filtered > pcm->spark.barometric_high) {
        value = pcm->spark.map_filtered;
        pcm->io.barometric_sample = value;
    } else {
        uint8_t flags = pcm->spark.load_status;
        if (flags & 0x40u) use_default = true;
        else if (flags & 0x0cu) {
            if (pcm->calibration->io == NULL) return PCM_BAD_CONFIGURATION;
            use_default = pcm->spark.map_filtered < pcm->calibration->io->map_default;
        }
        if (!use_default) {
            uint8_t rpm = pcm->spark.rpm_low_coordinate;
            uint8_t throttle = pcm->reference.throttle;
            uint8_t previous = (uint8_t)(pcm->fuel.throttle_decel_filter >> 8);
            uint8_t delta = throttle > previous ? (uint8_t)(throttle - previous) : (uint8_t)(previous - throttle);
            if (rpm <= cal->baro_rpm_upper && rpm >= cal->baro_rpm_lower &&
                pcm->reference.coolant >= cal->baro_coolant_minimum &&
                throttle > cal->baro_throttle_minimum && delta <= cal->baro_throttle_delta) {
                uint8_t row = (uint8_t)(((uint16_t)pcm->reference.rpm_coordinate * 171u + 128u) >> 8);
                if (row > 128u) row = 128;
                RUN(pcm_lookup2d(row, pcm->reference.throttle >> 1, &cal->baro_correction, &value));
                unsigned sum = (unsigned)value + pcm->spark.map_filtered;
                value = sum > 255u ? 255u : (uint8_t)sum;
                pcm->io.barometric_sample = value;
            } else {
                filter = false;
                value = pcm->spark.barometric_high;
                use_default = value == 0;
            }
        }
    }
    if (use_default) {
        if (pcm->calibration->io == NULL) return PCM_BAD_CONFIGURATION;
        value = pcm->calibration->io->map_default;
        pcm->io.barometric_sample = value;
        pcm->spark.barometric_high = value;
        pcm->io.barometric_fraction = 0;
    } else if (filter) {
        uint16_t old = (uint16_t)((uint16_t)pcm->spark.barometric_high * 256u + pcm->io.barometric_fraction);
        uint16_t filtered = pcm_lag8(value, old, cal->baro_gain);
        pcm->spark.barometric_high = (uint8_t)(filtered >> 8);
        pcm->io.barometric_fraction = (uint8_t)filtered;
        value = (uint8_t)(filtered >> 8);
    }
    value = value < 13u ? 143u : (uint8_t)(((uint16_t)(value - 13u) * 151u + 128u) >> 8);
    pcm->spark.barometric_pressure = value;
    uint8_t coordinate = value < 96u ? 0 : (uint8_t)(value - 96u);
    pcm->io.tps_ae_factor = pcm_lookup16(coordinate, cal->baro_ae);
    coordinate = pcm->spark.barometric_pressure < 96u ? 0 : (uint8_t)(pcm->spark.barometric_pressure - 96u);
    pcm->io.pe_throttle_threshold = pcm_lookup16(coordinate, cal->baro_pe_throttle);
    coordinate = pcm->spark.barometric_pressure < 96u ? 0 : (uint8_t)(pcm->spark.barometric_pressure - 96u);
    pcm->io.pe_rpm_threshold = pcm_lookup16(coordinate, cal->baro_pe_rpm);
    coordinate = pcm->spark.barometric_pressure < 96u ? 0 : (uint8_t)(pcm->spark.barometric_pressure - 96u);
    pcm->spark.normalized_load_divisor = pcm_lookup16(coordinate, cal->baro_load);
    return PCM_OK;
}
