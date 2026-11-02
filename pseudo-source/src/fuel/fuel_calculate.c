#include "fuel.h"
#include "delivery_internal.h"
/*7E4F..852B. Inputs/density are ready; the common852C tail is separate. */
PcmStatus pcm_fuel_calculate(Pcm *pcm)
{
    bool running;DL_RUN(pcm_fuel_admit(pcm,&running));
    return running ? pcm_fuel_running(pcm) : PCM_OK;
}
