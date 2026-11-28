#include "service.h"
#include "resident_transmission.h"
/* AE85..AE9C. Existing default dependency retained; a coherent logical
 * address provider may explicitly select the resident prefix. */
PcmStatus pcm_transmission_input_prefix(Pcm *pcm)
{
    if(pcm==NULL||pcm->platform==NULL) return PCM_BAD_CONFIGURATION;
    if(pcm->platform->enable_resident_transmission_input)
        return pcm_transmission_input_resident(pcm);
    return pcm_run_task(pcm,PCM_TRANSMISSION_INPUT_PREFIX);
}
