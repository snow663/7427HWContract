#include "fuel.h"
#include "feedback_internal.h"
#include "hardware.h"
/*877C..878F ->8911..891D. Retain the O2 filter's low fractional byte. */
PcmStatus pcm_oxygen_neutral(Pcm *pcm)
{
    pcm->fuel.integrator = 128;
    pcm->fuel.oxygen_filtered = (uint16_t)(0x6600u | (pcm->fuel.oxygen_filtered & 255u));
    pcm->fuel.integrator_delay = 0;
    pcm->fuel.proportional = 0;
    pcm->fuel.feedback_encoded = 0;
    return PCM_OK;
}
