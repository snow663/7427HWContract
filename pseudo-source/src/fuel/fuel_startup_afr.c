#include "fuel.h"
#include "mixture_internal.h"
#include "reference_math.h"
/* E3BB..E43B. The subsequent spark decay runs even when AFR decay is held. */
PcmStatus pcm_fuel_startup_afr(Pcm *pcm)
{
    if (pcm->fuel.startup_hold != 0) { --pcm->fuel.startup_hold; return PCM_OK; }
    if (pcm->fuel.startup_afr == 0) return PCM_OK;
    MIX_CAL();
    uint8_t hold = pcm->fuel.startup_park_hold;
    if (hold != 0) {
        if (hold == cal->startup_park_hold && pcm->reference.coolant <= cal->startup_coolant_limit && pcm->iac.park_neutral) return PCM_OK;
        pcm->fuel.startup_park_hold = --hold;
        if (hold != 0) return PCM_OK;
        pcm->io.coolant_context |= 8u;
    }
    if (pcm->fuel.startup_interval != 0) { --pcm->fuel.startup_interval; return PCM_OK; }
    pcm->fuel.startup_interval = pcm_lookup16(pcm->reference.coolant, cal->startup_interval);
    pcm->fuel.startup_interval = mix_double(pcm->fuel.startup_interval, pcm_lookup16(mix_min(pcm->iac.runtime_high, 64), cal->startup_air));
    uint8_t value = (uint8_t)(((uint16_t)pcm->fuel.startup_afr * cal->startup_afr_gain) >> 8);
    if (!(pcm->io.coolant_context & 8u) && value <= cal->startup_afr_limit && pcm->reference.coolant <= cal->startup_coolant_limit)
        pcm->fuel.startup_park_hold = cal->startup_park_hold;
    pcm->fuel.startup_afr = value;
    return PCM_OK;
}
