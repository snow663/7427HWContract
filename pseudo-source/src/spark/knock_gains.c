#include "knock.h"
#include "reference_math.h"
/* CAD5..CB14: three separate RPM samples and the entry PE/load-status gates.
 * MAT and PE-spark production at CA6B..CAD4 remain outside this callable slice. */
PcmStatus pcm_knock_gains(Pcm *pcm)
{
    if (pcm->calibration == NULL) return PCM_BAD_CONFIGURATION;
    const PcmKnockCalibration *cal = &pcm->calibration->knock;
    pcm->knock.octane_rpm_factor = pcm_lookup16((uint8_t)(pcm->reference.rpm_coordinate >> 1), cal->octane_rpm);
    pcm->knock.event_gain = pcm_lookup16(pcm->reference.rpm_coordinate, cal->event_gain_curve);
    uint8_t input;
    const uint8_t *knots;
    if (pcm->runtime.power_enrichment) {
        input = (uint8_t)(pcm->reference.rpm_coordinate >> 1);
        input = input >= 16u ? (uint8_t)(input - 16u) : 0;
        knots = cal->pe_retard_cap;
    } else {
        uint8_t source = 255;
        if (!(pcm->spark.load_status & 0x48u)) source = pcm->spark.vacuum;
        input = (uint8_t)(source >> 1);
        input = input >= 32u ? (uint8_t)(input - 32u) : 0;
        knots = cal->cruise_retard_cap;
    }
    pcm->knock.retard_limit = pcm_lookup16(input, knots);
    return PCM_OK;
}
