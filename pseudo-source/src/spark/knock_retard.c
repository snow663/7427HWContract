#include "knock.h"
/* AA81..AADB. Callable slice within the implemented resident A466 spark root.
 * The original stack byte at AACF..AADB becomes a local subtraction value. */
PcmStatus pcm_knock_retard(Pcm *pcm)
{
    if (pcm->calibration == NULL) return PCM_BAD_CONFIGURATION;
    PcmStatus result = pcm_mask_irq(pcm, true);
    if (result != PCM_OK) return result;
    uint8_t observations = pcm->knock.observation_accumulator;
    pcm->knock.observation_accumulator = 0;
    result = pcm_mask_irq(pcm, false);
    if (result != PCM_OK) return result;
    const PcmKnockCalibration *cal = &pcm->calibration->knock;
    uint8_t retard;
    if (pcm->knock.burst_active ||
        (!(pcm->runtime.primary_faults & 0x60u) && pcm->reference.coolant < cal->minimum_coolant)) {
        retard = 0;
    } else {
        if (pcm->spark.vehicle_speed_high < cal->minimum_speed && pcm->spark.rpm_high < cal->minimum_rpm_high)
            return PCM_OK; /* Retain old020C but do not subtract it on this call. */
        if (pcm->knock.sensor_fault) retard = cal->fault_retard;
        else {
            uint32_t doubled = (uint32_t)pcm->knock.event_gain * observations * 2u;
            uint16_t candidate;
            if (doubled > 65535u) candidate = 255; /* ASLD carry skips old020C. */
            else {
                candidate = (uint16_t)(doubled >> 8) + pcm->knock.retard;
                if (candidate > 255u) candidate = 255;
            }
            uint8_t limit = pcm->knock.retard_limit;
            retard = candidate < limit ? (uint8_t)candidate : limit;
        }
    }
    pcm->knock.retard = retard;
    pcm->spark.command = (uint16_t)(pcm->spark.command - (retard >> 1));
    return PCM_OK;
}
