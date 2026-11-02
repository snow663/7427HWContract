#include "fuel.h"
#include "delivery_internal.h"
#include "hardware.h"
/*Contiguous7EB2..852B. Broad admission/ignition and852C scheduling stay explicit. */
PcmStatus pcm_fuel_running(Pcm *pcm)
{
    DL_RUN(pcm_fuel_construct(pcm));return pcm_fuel_deliver(pcm);
}
