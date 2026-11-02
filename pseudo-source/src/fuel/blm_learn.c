#include "fuel.h"
#include "feedback_internal.h"
#include "hardware.h"
/*8E1D..8EB3. The selected cell must be in0..20 at an admitted write.
 * Invalid direct-call indices return a configuration boundary after counters. */
PcmStatus pcm_blm_learn(Pcm *pcm)
{
    if (!(pcm->io.coolant_context & 2u) || pcm->fuel.blm_cell_changed || pcm->fuel.integrator == 128) goto reset;
    uint8_t count = (uint8_t)(pcm->fuel.blm_interval_count+1u);
    if (!(count & 128u)) {
        pcm->fuel.blm_interval_count = count;
        if (2u*count < pcm->fuel.oxygen_interval) goto finish;
    }
    count = (uint8_t)(pcm->fuel.blm_learning_count+1u);
    FB_CAL();
    if (count != 0) {
        pcm->fuel.blm_learning_count = count;
        if (count < cal->learning_delay) goto finish;
    }
    uint8_t index = pcm->iac.blm_cell_index;
    bool negative = pcm->fuel.integrator < 128;
    uint8_t error = negative ? (uint8_t)(128-pcm->fuel.integrator) : (uint8_t)(pcm->fuel.integrator-128);
    if (error <= cal->learning_error[index<16 ? 0 : 1] || negative != ((pcm->io.coolant_context & 0x40u) != 0)) goto finish;
    if (index>=21) return PCM_BAD_CONFIGURATION;
    uint8_t value = pcm->fuel.blm_cells[index];
    if (negative) {
        uint8_t lower = cal->blm_minimum[index<16 ? 0 : 1];
        if (value < cal->learning_step || value-cal->learning_step < lower) value = lower;
        else value = (uint8_t)(value-cal->learning_step);
    } else {
        unsigned candidate = (unsigned)value+cal->learning_step;
        value = candidate>255u || candidate>cal->blm_maximum ? cal->blm_maximum : (uint8_t)candidate;
    }
    pcm->fuel.blm_cells[index] = value;pcm->iac.blm_value = value;
reset:
    pcm->fuel.blm_interval_count = 0;pcm->fuel.blm_learning_count = 0;
finish:
    pcm->fuel.blm_cell_changed = false;
    pcm->io.map_previous_rpm = pcm->spark.rpm_high;
    pcm->fuel.previous_oxygen = pcm->fuel.raw_oxygen;
    return PCM_OK;
}
