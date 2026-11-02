#include "fuel.h"
#include "feedback_internal.h"
#include "hardware.h"
/*863D..8661. Raw O2 activity is distinct from direction and filtered O2. */
PcmStatus pcm_oxygen_activity(Pcm *pcm)
{
    if (!pcm->runtime.fuel_running) return PCM_OK;
    FB_CAL();
    unsigned index = (pcm->spark.idle_state ? 4u : 0u) + ((pcm->io.coolant_context & 0x80u) ? 0u : 2u);
    uint8_t sample = pcm->fuel.raw_oxygen;
    if (sample > cal->activity[index] || sample < cal->activity[index+1u]) {
        pcm->fuel.oxygen_age = 0;
        pcm->fuel.oxygen_activity = true;
    }
    return PCM_OK;
}
