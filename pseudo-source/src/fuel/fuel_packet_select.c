#include "fuel.h"
#include "delivery_internal.h"
#include "hardware.h"
/*8476..84A8 or84B6..84BB. Selection debits RAM before the masked emission. */
PcmStatus pcm_fuel_packet_select(Pcm *pcm, uint16_t *packet, bool *emit)
{
    if (packet==NULL || emit==NULL) return PCM_BAD_CONFIGURATION;
    *emit=false;
    uint16_t accumulated=dl_accumulator(pcm), total=(uint16_t)(accumulated+pcm->fuel.acceleration_reservoir);
    DL_CAL();
    if (total>cal->packet_maximum) {
        uint16_t remaining=(uint16_t)(accumulated-cal->packet_maximum);
        if (accumulated<cal->packet_maximum) {
            pcm->fuel.acceleration_reservoir=(uint16_t)(remaining+pcm->fuel.acceleration_reservoir);remaining=0;
        }
        dl_store_accumulator(pcm,remaining);*packet=cal->packet_maximum;
    } else if (total<=cal->packet_minimum) {
        pcm->fuel.async_suppressed=true;pcm->fuel.async_pending=false;return PCM_OK;
    } else {
        pcm->fuel.acceleration_reservoir=0;dl_store_accumulator(pcm,0);*packet=total;
    }
    *emit=true;return PCM_OK;
}
