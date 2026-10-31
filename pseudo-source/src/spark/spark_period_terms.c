#include "spark.h"
#include "hardware.h"
/* A687..A6FF: N-bit adaptive adoption, unsigned cap, reference/battery sum,
 * then a fresh3FC0 limit read. Stores preceding a failed read remain visible. */
PcmStatus pcm_spark_period_terms(Pcm *pcm)
{
    uint8_t load = pcm->spark.load_coordinate;
    uint8_t old_load = pcm->spark.previous_load;
    uint8_t delta = (uint8_t)(load - old_load);
    if (load >= old_load && delta >= 32u) pcm->spark.adaptive_period = (uint16_t)(0xff00u | delta);
    else {
        uint16_t previous = pcm->spark.previous_period;
        uint16_t period = pcm->spark.period;
        uint16_t candidate = (uint16_t)((uint16_t)(previous - period) * 2u);
        if (!((uint16_t)(candidate - pcm->spark.adaptive_period) & 0x8000u))
            pcm->spark.adaptive_period = candidate;
    }
    uint16_t cap = pcm->spark.period >> 3;
    if (pcm->spark.adaptive_period > cap) pcm->spark.adaptive_period = cap;
    uint16_t period = pcm->spark.period;
    pcm->spark.previous_period = period;
    pcm->spark.reference_term = pcm_spark_reference_term(period);
    uint8_t battery = pcm->spark.battery_sample;
    uint16_t battery_term = battery <= 120u ? (uint16_t)((120u - battery) * 4u) : 0u;
    uint16_t sum = (uint16_t)(battery_term + pcm->spark.reference_term);
    pcm->spark.period_correction = (uint16_t)(sum + pcm->spark.adaptive_period);
    uint16_t fresh_period;
    PcmStatus result = pcm_read16(pcm, PCM_REFERENCE_PERIOD, &fresh_period);
    if (result != PCM_OK) return result;
    uint16_t limit = (uint16_t)(fresh_period - 39u);
    if (pcm->spark.period_correction > limit) pcm->spark.period_correction = limit;
    return PCM_OK;
}
