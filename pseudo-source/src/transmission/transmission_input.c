#include "control.h"
#include "service.h"
/*AE85..AEA3. Earlier input/control work remains an explicit prefix dependency. */
PcmStatus pcm_transmission_input(Pcm *pcm)
{
    PcmStatus result=pcm_transmission_input_prefix(pcm);if (result!=PCM_OK) return result;
    return pcm_serial_service_poll(pcm);
}
