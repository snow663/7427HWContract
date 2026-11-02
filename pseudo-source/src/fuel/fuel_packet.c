#include "fuel.h"
#include "delivery_internal.h"
#include "hardware.h"
/*8476..84BB. The finalizer at84BC is a separate successor. */
PcmStatus pcm_fuel_packet(Pcm *pcm)
{
    uint16_t packet;bool emit;DL_RUN(pcm_fuel_packet_select(pcm,&packet,&emit));
    return emit ? pcm_fuel_packet_emit(pcm,packet) : PCM_OK;
}
