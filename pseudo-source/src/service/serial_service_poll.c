#include "service_internal.h"
/*AE9D..AEA3. No controller calculation is inserted between expiry and service. */
PcmStatus pcm_serial_service_poll(Pcm *pcm)
{
    SVC_RUN(pcm_serial_idle(pcm));return pcm_serial_service(pcm);
}
