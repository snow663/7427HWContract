#include "fuel.h"
#include "reference_math.h"
/*7F86..7FD7. Lookup neighbors remain in the bounded source views, even at
 * zero-weight endpoints. An idle return can request the existing O2 reset. */
PcmStatus pcm_fuel_ve(Pcm *pcm)
{
    if (pcm->calibration == NULL || pcm->calibration->air == NULL) return PCM_BAD_CONFIGURATION;
    const PcmAirCalibration *cal = pcm->calibration->air;
    uint8_t load = pcm->spark.load_coordinate;
    if (load > 64u) load = (uint8_t)(((unsigned)load + 1u) / 2u + 32u);
    uint8_t value;
    PcmStatus result;
    if (pcm->reference.throttle >= pcm->calibration->reference.throttle_limit ||
        pcm->spark.vehicle_speed_high >= cal->ve_speed_limit || pcm->reference.rpm_coordinate >= 72u) {
        pcm->fuel.open_ve = true;
        result = pcm_lookup2d(pcm->reference.rpm_coordinate, load, &cal->ve_open, &value);
    } else {
        uint8_t rpm = pcm->spark.rpm_high;
        if (rpm > 144u) rpm = 144;
        result = pcm_lookup2d(rpm, load, &cal->ve_idle, &value);
        if (result != PCM_OK) return result;
        if (pcm->fuel.open_ve) {
            if (pcm->fuel.integrator <= cal->ve_integrator_limit) pcm->fuel.ve_reset_request = true;
            pcm->fuel.open_ve = false;
        }
    }
    if (result != PCM_OK) return result;
    pcm->fuel.volumetric_efficiency = value;
    return PCM_OK;
}
