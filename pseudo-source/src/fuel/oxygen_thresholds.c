#include "fuel.h"
#include "feedback_internal.h"
#include "hardware.h"
/*8662..86AF. Input128 still reads the next curve's first knot. */
PcmStatus pcm_oxygen_thresholds(Pcm *pcm)
{
    FB_CAL();
    pcm->fuel.oxygen_coordinate = mix_min(mix_byte(((uint32_t)pcm->iac.runtime_high * cal->airflow_gain) >> 6), 128);
    uint8_t value = pcm->fuel.oxygen_coordinate;
    if (pcm->spark.idle_state) {
        pcm->fuel.oxygen_upper = cal->idle_thresholds[0];
        pcm->fuel.oxygen_lower = cal->idle_thresholds[1];
        pcm->fuel.oxygen_center = cal->idle_center;
    } else {
        pcm->fuel.oxygen_lower = pcm_lookup16(value, cal->oxygen[3]);
        pcm->fuel.oxygen_upper = pcm_lookup16(value, cal->oxygen[2]);
        pcm->fuel.oxygen_center = pcm_lookup16(value, cal->oxygen[1]);
    }
    uint8_t interval = pcm_lookup16(pcm->fuel.oxygen_coordinate, cal->oxygen[0]);
    pcm->fuel.oxygen_interval = pcm->fuel.alternate_interval ? cal->alternate_interval : interval;
    return PCM_OK;
}
