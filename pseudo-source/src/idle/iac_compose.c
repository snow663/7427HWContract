#include "iac.h"
#include "iac_math.h"
#include "reference_math.h"
/* 9752..983C and the common conversion tail. Each clamp is ordered. */
PcmStatus pcm_iac_compose(Pcm *pcm)
{
    if (pcm->calibration == NULL || pcm->calibration->iac == NULL) return PCM_BAD_CONFIGURATION;
    const PcmIacCalibration *cal = pcm->calibration->iac;
    uint16_t flow = iac_cap((uint32_t)pcm->iac.selected_integral + pcm->iac.selected_cold);
    flow = (pcm->iac.context & 0x80u) ? iac_sub_high(flow, pcm->iac.proportional) : iac_add_high(flow, pcm->iac.proportional);
    flow = (pcm->iac.kicker_flags & 0x80u) ? iac_add_high(flow, pcm->iac.derivative) : iac_sub_high(flow, pcm->iac.derivative);
    uint32_t sum = (uint32_t)flow + ((uint32_t)pcm->iac.startup_flow << 8);
    if (sum <= 65535u) sum += (uint32_t)pcm->iac.switch_adder << 8;
    flow = iac_cap(sum);
    flow = (pcm->iac.context & 1u) ? iac_add_high(flow, pcm->iac.ac_adder) : iac_sub_high(flow, pcm->iac.ac_adder);
    flow = iac_add_high(flow, pcm->iac.gear_adder);
    uint16_t old = pcm->iac.composite_flow;pcm->iac.composite_flow = flow;
    uint8_t enrichment = 0;
    if (pcm->reference.throttle < cal->enrichment_throttle && flow >= old && ((flow - old) >> 8) >= cal->enrichment_flow) {
        uint16_t increase = iac_cap(4u * (uint32_t)(flow - old));
        PcmStatus result = pcm_lookup_scaled((uint8_t)(increase >> 8), &cal->enrichment_curve, &enrichment);
        if (result != PCM_OK) return result;
    }
    pcm->iac.enrichment = enrichment;
    sum = (uint32_t)flow + (pcm->iac.follower & 0xff00u);
    if (sum > 65535u) flow = UINT16_MAX;
    else {
        flow = (uint16_t)sum;
        if (pcm->runtime.deceleration_fuel_cut) {
            uint8_t amount = pcm_lookup16(pcm->reference.rpm_coordinate, cal->dfco_curve);
            if (amount < cal->dfco_bias) { pcm->iac.transfer_flags |= 0x20u;amount = (uint8_t)(cal->dfco_bias - amount); }
            else { pcm->iac.transfer_flags &= (uint8_t)~0x20u;amount = (uint8_t)(amount - cal->dfco_bias); }
            pcm->iac.dfco_adder = amount;pcm->iac.dfco_divider = cal->dfco_decay_reload;
        }
        flow = (pcm->iac.transfer_flags & 0x20u) ? iac_sub_high(flow, pcm->iac.dfco_adder) : iac_add_high(flow, pcm->iac.dfco_adder);
    }
    if (pcm->runtime.power_enrichment && flow > cal->pe_flow_limit) flow = cal->pe_flow_limit;
    return pcm_iac_convert(pcm, flow);
}
