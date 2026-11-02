#include "fuel.h"
#include "mixture_internal.h"
#include "reference_math.h"
/* 8C38..8C72. Optional1800 stays an explicit dependency; no BLM work is skipped. */
PcmStatus pcm_fuel_afr_finish(Pcm *pcm)
{
    pcm->fuel.pe_previous_throttle = pcm->reference.throttle;
    if (pcm->fuel.output_rich_cap) {
        MIX_CAL();
        uint8_t cap = pcm_lookup16(pcm->iac.runtime_high, cal->output_rich_limit);
        if (cap <= pcm->fuel.commanded_afr) pcm->fuel.commanded_afr = cap;
    }
    if (pcm->runtime.engine_service && (pcm->spark.service_flags & 4u)) pcm->fuel.commanded_afr = pcm->fuel.service_afr;
    else if (pcm->scheduler.profiling_enabled) { MIX_RUN(pcm_run_task(pcm, PCM_AFR_EXTENSION)); }
    pcm->fuel.published_afr = pcm->fuel.commanded_afr;
    return PCM_OK;
}
