#include "knock.h"
#include "reference_math.h"
/* CA4C..CA6A ->CB14: temperature transform, rounded gain153 and F499 cap.
 * Coolant is a byte, so max(coolant-153,0)<=102 before the two shifts. */
PcmStatus pcm_burst_gain(Pcm *pcm)
{
    if (pcm->calibration == NULL) return PCM_BAD_CONFIGURATION;
    uint8_t coolant = pcm->reference.coolant;
    uint16_t transformed = coolant > 153u ? (uint16_t)(coolant - 153u) * 4u : 0;
    if (transformed > 255u) transformed = 255;
    uint8_t input = (uint8_t)((transformed * 153u + 128u) >> 8);
    const PcmKnockCalibration *cal = &pcm->calibration->knock;
    if (input > cal->burst_table_limit) input = cal->burst_table_limit;
    pcm->knock.burst_gain = pcm_lookup16(input, cal->burst_curve);
    return PCM_OK;
}
