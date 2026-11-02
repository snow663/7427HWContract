#include "service_internal.h"
/*F64E..F780, with every intermediate stage retained in source order. */
PcmStatus pcm_serial_service(Pcm *pcm)
{
    SVC_RUN(pcm_service_status(pcm));SVC_RUN(pcm_service_transmission(pcm));
    SVC_RUN(pcm_service_engine(pcm));SVC_RUN(pcm_service_clear(pcm));return pcm_service_cleanup(pcm);
}
