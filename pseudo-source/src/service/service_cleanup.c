#include "service_internal.h"
/*F76A..F77F. Clear-edge consumption precedes engine cleanup. */
PcmStatus pcm_service_cleanup(Pcm *pcm)
{
    if (pcm->runtime.engine_service && (!(pcm->serial.sessions&1u) || pcm->serial.service_expiry!=0)) {
        pcm->runtime.engine_service=false;pcm->serial.engine_command=0;pcm->runtime.output_override=false;
    }
    return PCM_OK;
}
