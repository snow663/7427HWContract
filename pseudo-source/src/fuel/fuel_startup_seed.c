#include "fuel.h"
#include "mixture_internal.h"
#include "reference_math.h"
/* E340..E38E. The caller selected nonrunning mode;0004.3 suppresses reseeding. */
PcmStatus pcm_fuel_startup_seed(Pcm *pcm)
{
    MIX_CAL();
    uint8_t value;
    if (!pcm->spark.run_transition) {
        pcm->fuel.startup_afr = pcm_lookup16(pcm->reference.coolant, cal->startup_afr);
        MIX_RUN(pcm_lookup_scaled(pcm->reference.coolant, &cal->startup_spark, &value));
        pcm->spark.startup_adder = value;
        MIX_RUN(pcm_lookup_scaled(pcm->reference.coolant, &cal->startup_spark_delay, &value));
        pcm->fuel.startup_spark_delay = value;
        pcm->reference.enrichment = pcm_lookup16(pcm->reference.coolant, cal->startup_ref);
        pcm->fuel.startup_hold = cal->startup_hold;
    }
    pcm->reference.enrichment_decrement = pcm_lookup16(pcm->reference.coolant, cal->startup_decrement);
    MIX_RUN(pcm_lookup_scaled(pcm->reference.coolant, &cal->startup_spark_gain, &value));
    pcm->fuel.startup_spark_gain = value;
    return PCM_OK;
}
