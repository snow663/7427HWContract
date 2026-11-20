#include "pcm.h"
#include "fuel_ram_owners.h"
/* One atomic logical word callback. Named word state changes only after
 * the backing provider accepts the full transaction. */
PcmStatus pcm_write16(Pcm *pcm,uint16_t address,uint16_t value)
{
    if(pcm->platform==NULL || pcm->platform->write16==NULL)return PCM_NO_HARDWARE;
    PcmStatus status=pcm->platform->write16(pcm->platform->context,address,value);
    if(status==PCM_OK && pcm->platform->bind_fuel_ram_owners)
        (void)pcm_fuel_ram_owner_write16(pcm,address,value);
    return status;
}
