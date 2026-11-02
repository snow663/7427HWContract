#include "fuel.h"
#include "feedback_internal.h"
#include "hardware.h"
/*86B0..86F1. In-band direction follows the previous AFR-task sample. */
PcmStatus pcm_oxygen_direction(Pcm *pcm)
{
    FB_CAL();
    uint8_t old = pcm->io.coolant_context;
    unsigned high = (unsigned)pcm->fuel.oxygen_center + cal->direction_band;
    bool direction;
    if (high <= 255u && high < pcm->fuel.raw_oxygen) direction = true;
    else if (pcm->fuel.oxygen_center >= cal->direction_band &&
             pcm->fuel.oxygen_center - cal->direction_band > pcm->fuel.raw_oxygen) direction = false;
    else direction = pcm->fuel.raw_oxygen > pcm->fuel.previous_oxygen;
    uint8_t next = (uint8_t)((old & 0xbfu) | (direction ? 0x40u : 0u));
    if (next != pcm->io.coolant_context) {
        ++pcm->fuel.oxygen_changes;
        pcm->fuel.oxygen_changed = true;
        pcm->fuel.oxygen_direction_age = 0;
    } else if (pcm->fuel.oxygen_direction_age != 255) ++pcm->fuel.oxygen_direction_age;
    pcm->io.coolant_context = next;
    return PCM_OK;
}
