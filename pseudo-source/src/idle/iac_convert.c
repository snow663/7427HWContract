#include "iac.h"
#include "iac_math.h"
#include "reference_math.h"
/* 983D..989B. Position lookup uses wrapped increasing delta, including the
 * endpoint's neighboring byte; it is deliberately not pcm_lookup16. */
PcmStatus pcm_iac_convert(Pcm *pcm, uint16_t flow)
{
    pcm->iac.pre_baro_flow = flow;
    if (pcm->calibration == NULL || pcm->calibration->iac == NULL) return PCM_BAD_CONFIGURATION;
    const PcmIacCalibration *cal = pcm->calibration->iac;
    uint8_t gain;
    PcmStatus result = pcm_lookup_offset(pcm->spark.barometric_pressure, &cal->baro, &gain);
    if (result != PCM_OK) return result;
    flow = iac_cap(2u * (uint32_t)pcm_gain_word(pcm->iac.pre_baro_flow, gain));
    if (cal->options & 4u) {
        if ((pcm->iac.kicker_flags & 4u) && (flow >> 8) < cal->kicker_flow_subtract) {
            pcm->iac.kicker_flags |= 8u;flow = 0;
        } else {
            if (pcm->iac.kicker_flags & 4u) flow = (uint16_t)(flow - ((uint16_t)cal->kicker_flow_subtract << 8));
            flow = iac_cap((uint32_t)flow + pcm_gain_word(flow, cal->kicker_flow_gain));
        }
    }
    pcm->iac.airflow = flow;
    uint16_t coordinate = (uint16_t)(((uint32_t)flow + 8u) >> 4);
    unsigned index = coordinate >> 8;
    uint8_t first = cal->position_curve[index];
    uint8_t delta = (uint8_t)(cal->position_curve[index + 1u] - first);
    uint8_t step = (uint8_t)(((uint16_t)delta * (uint8_t)coordinate + 128u) >> 8);
    pcm->iac.target = (uint8_t)(first + step);
    return PCM_OK;
}
