#include "fuel.h"
#include "delivery_internal.h"
#include "hardware.h"
/*Contiguous83B1..852B. Returns immediately before the common852C tail. */
PcmStatus pcm_fuel_deliver(Pcm *pcm)
{
    bool packet;DL_RUN(pcm_fuel_route(pcm,&packet));
    if (packet) { DL_RUN(pcm_fuel_packet(pcm)); }
    return pcm_fuel_finalize(pcm);
}
