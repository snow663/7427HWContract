#include "fuel.h"
#include "mixture_internal.h"
#include "reference_math.h"
/* E43C..E476. Delay counts only phase00..0F; later reduction counts every call. */
PcmStatus pcm_fuel_startup_spark(Pcm *pcm)
{
    if (pcm->fuel.startup_spark_delay != 0) {
        if (!(pcm->scheduler.phase & 0xf0u)) --pcm->fuel.startup_spark_delay;
        return PCM_OK;
    }
    if (pcm->spark.startup_adder == 0) return PCM_OK;
    if (pcm->fuel.startup_spark_interval != 0) { --pcm->fuel.startup_spark_interval; return PCM_OK; }
    MIX_CAL();
    pcm->fuel.startup_spark_interval = pcm_lookup16(mix_min(pcm->iac.runtime_high, 64), cal->spark_air);
    pcm->spark.startup_adder = (uint8_t)(((uint16_t)pcm->spark.startup_adder * pcm->fuel.startup_spark_gain) >> 8);
    return PCM_OK;
}
