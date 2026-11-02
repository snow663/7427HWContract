#include "fuel.h"
#include "mixture_internal.h"
#include "reference_math.h"
/* 8DEF..8E1C; word histories feed AE, decel and BARO without duplicating TPS. */
PcmStatus pcm_fuel_decel_history(Pcm *pcm)
{
    if (pcm->fuel.history_count != 0) { --pcm->fuel.history_count; return PCM_OK; }
    MIX_CAL();
    pcm->fuel.history_count = cal->history_reload;
    pcm->fuel.throttle_decel_filter = pcm_lag8(pcm->reference.throttle, pcm->fuel.throttle_decel_filter, cal->history_gain);
    pcm->fuel.map_history = pcm_lag8(pcm->spark.load_coordinate, pcm->fuel.map_history, pcm->io.environmental_idle);
    return PCM_OK;
}
