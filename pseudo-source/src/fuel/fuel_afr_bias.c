#include "fuel.h"
#include "mixture_internal.h"
/* 8A22..8A8A. Additional REF-counted enrichment is applied after the upper cap. */
PcmStatus pcm_fuel_afr_bias(Pcm *pcm, uint8_t value)
{
    MIX_CAL();
    if (!(pcm->io.coolant_context & 0x80u)) {
        if (pcm->scheduler.clear_after_run_count) value = mix_sub(value, cal->hotstart_subtract);
        uint8_t coolant = pcm->reference.coolant;
        if (coolant > cal->warm_coolant[0] && coolant < cal->warm_coolant[1]) {
            if (pcm->iac.park_neutral) value = mix_sub(value, cal->warm_park_subtract);
            else if (pcm->fuel.warm_afr_count <= cal->warm_duration) {
                if (pcm->fuel.warm_afr_count != 255) ++pcm->fuel.warm_afr_count;
                value = mix_sub(value, cal->warm_drive_subtract);
            }
        }
    }
    value = mix_min(value, pcm->fuel.alternate_afr_limit ? cal->afr_alternate_maximum : cal->afr_maximum);
    if (pcm->reference.enrichment_age >= cal->enrichment_age) {
        if (pcm->reference.coolant <= cal->enrichment_coolant) value = mix_sub(value, pcm->reference.enrichment);
        else value = mix_byte((unsigned)value + pcm->reference.enrichment);
    }
    pcm->fuel.commanded_afr = value;
    return PCM_OK;
}
