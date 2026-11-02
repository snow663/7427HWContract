#include "service.h"
/*AE85..AE9C: AEA4,B018,B089,C483,B1F0,B23C,B2C9,B2ED in that order.
 * This boundary supplies all eight callees, not the later idle/service bodies. */
PcmStatus pcm_transmission_input_prefix(Pcm *pcm)
{
    return pcm_run_task(pcm,PCM_TRANSMISSION_INPUT_PREFIX);
}
