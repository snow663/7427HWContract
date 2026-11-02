#include "fuel.h"
#include "delivery_internal.h"
#include "hardware.h"
/*810C..8174. Saturated byte additions precede a wrapping word reservoir. */
PcmStatus pcm_fuel_acceleration_reservoir(Pcm *pcm)
{
    DL_CAL();
    unsigned value=pcm->iac.enrichment;
    if (pcm->io.coolant_context & 1u) {
        pcm->io.coolant_context &= 0xfeu;value+=cal->transition_enrichment;
        if (value>255u) goto saturated;
    }
    if (!pcm->io.ac_mirror) pcm->fuel.ac_enrichment_seen=false;
    else if (!pcm->fuel.ac_enrichment_seen) {
        pcm->fuel.ac_enrichment_seen=true;value+=cal->ac_enrichment;
        if (value>255u) goto saturated;
    }
    value+=pcm->fuel.tps_ae;
saturated:
    value=mix_byte(value);
    if (value!=0) pcm->fuel.acceleration_reservoir=(uint16_t)(pcm->fuel.acceleration_reservoir+((value*pcm->fuel.tps_ae_gain)>>3));
    if (value!=0 || pcm->fuel.map_acceleration) {
        if (!pcm->fuel.acceleration_active) pcm->fuel.enrichment_entry=true;
        pcm->fuel.acceleration_active=true;pcm->fuel.async_pending=true;
        pcm->fuel.asynchronous_active=true;pcm->fuel.fuel_activity=true;
        pcm->fuel.acceleration_hold=cal->acceleration_hold;
    } else {
        pcm->fuel.acceleration_active=false;
        if (pcm->fuel.acceleration_hold!=0) --pcm->fuel.acceleration_hold;
        else pcm->fuel.fuel_activity=false;
    }
    return PCM_OK;
}
