#include "fuel.h"
#include "feedback_internal.h"
#include "hardware.h"
/*8790..886E. The P-window is a stack temporary, exposed as an output. */
PcmStatus pcm_oxygen_proportional(Pcm *pcm, uint8_t *window)
{
    if (window == NULL) return PCM_BAD_CONFIGURATION;
    uint8_t sample = (uint8_t)(pcm->fuel.oxygen_filtered >> 8), error;
    FB_CAL();
    if (sample > pcm->fuel.oxygen_upper) {
        error = (uint8_t)(((uint16_t)(sample-pcm->fuel.oxygen_upper)*cal->positive_error_gain) >> 8);
        pcm->fuel.oxygen_error_positive = true;
    } else if (sample < pcm->fuel.oxygen_lower) {
        error = (uint8_t)(pcm->fuel.oxygen_lower-sample);
        pcm->fuel.oxygen_error_positive = false;
    } else { error = 0; goto store_error; }
    if (pcm->spark.idle_state) error = (uint8_t)(((uint16_t)error*cal->idle_error_gain) >> 8);
    error = mix_min(error, 96);
store_error:
    pcm->fuel.oxygen_error = error;
    pcm->fuel.proportional = pcm_lookup16((uint8_t)(2u*error), cal->error_curve);
    uint8_t base, value;
    if (pcm->spark.idle_state) {
        base = cal->idle_base_delay;
        if (!(pcm->io.coolant_context & 0x40u)) {
            FB_RUN(pcm_mask_irq(pcm, true));
            pcm->fuel.startup_context ^= 5u;
            FB_RUN(pcm_mask_irq(pcm, false));
        }
        uint8_t context = pcm->fuel.startup_context;
        bool paired = (context & 3u) == 3u || (context & 12u) == 12u;
        pcm->fuel.idle_oxygen_interval = cal->idle_interval[paired ? 0 : 1];
        unsigned index = paired ? ((pcm->io.coolant_context & 0x40u) ? 0u : 1u) : 2u;
        value = (uint8_t)(mix_word(4u*(uint32_t)cal->idle_coefficient[index]*pcm->fuel.proportional) >> 8);
    } else {
        base = pcm_lookup16(pcm->fuel.oxygen_coordinate, cal->base_delay);
        FB_RUN(pcm_lookup2d(mix_min(pcm->reference.rpm_coordinate,144), (uint8_t)(pcm->spark.load_coordinate>>1), &cal->proportional, &value));
        value = mix_double_round(value, pcm->fuel.proportional);
    }
    pcm->fuel.proportional = value;
    uint8_t duration = mix_byte((unsigned)base+pcm_lookup16((uint8_t)(2u*pcm->fuel.oxygen_error),cal->error_delay));
    value = (uint8_t)(((uint16_t)pcm_lookup16((uint8_t)(2u*pcm->fuel.oxygen_error),cal->interval_gain)*pcm->fuel.oxygen_interval)>>8);
    if (pcm->spark.idle_state) value = mix_byte((unsigned)value+pcm->fuel.idle_oxygen_interval);
    pcm->fuel.oxygen_interval = value;
    pcm->fuel.interval_snapshot = value;
    *window = duration;
    return PCM_OK;
}
