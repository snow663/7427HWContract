#include "fuel.h"
#include "delivery_internal.h"
#include "hardware.h"
/*84A9..84B5. Literal SEI/CLI; no automatic mask restoration after failure. */
PcmStatus pcm_fuel_packet_emit(Pcm *pcm, uint16_t packet)
{
    DL_RUN(pcm_mask_irq(pcm,true));DL_RUN(pcm_fuel_async(pcm,packet));DL_RUN(pcm_mask_irq(pcm,false));
    pcm->fuel.async_pending=true;pcm->fuel.async_suppressed=false;return PCM_OK;
}
