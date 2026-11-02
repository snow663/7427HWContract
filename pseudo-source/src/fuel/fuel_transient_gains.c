#include "fuel.h"
#include "mixture_internal.h"
#include "reference_math.h"
/* E30B..E33B; injector offset ends atE305, intervening E306..E30A is separate. */
PcmStatus pcm_fuel_transient_gains(Pcm *pcm)
{
    MIX_CAL();
    uint8_t value;
    MIX_RUN(pcm_lookup_scaled(pcm->reference.coolant, &cal->ae_base, &value));
    pcm->fuel.base_ae_gain = value;
    uint8_t cold = pcm_lookup16(pcm->reference.coolant, cal->ae_coolant);
    pcm->fuel.tps_ae_gain = mix_double(cold, pcm_lookup16(pcm->spark.mat_sample, cal->ae_mat));
    pcm->fuel.map_ae_gain = pcm_lookup16(pcm->reference.coolant, cal->ae_map_gain);
    return PCM_OK;
}
