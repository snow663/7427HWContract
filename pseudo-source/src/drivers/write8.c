#include "pcm.h"
#include "fuel_ram_owners.h"
/* Commit to the external address provider FIRST, and then mirror only
 * the owned fields. A failed bus write cannot modify C owner state. */
PcmStatus pcm_write8(Pcm *pcm,uint16_t address,uint8_t value)
{
    if(pcm->platform==NULL || pcm->platform->write8==NULL)return PCM_NO_HARDWARE;
    PcmStatus status=pcm->platform->write8(pcm->platform->context,address,value);
    if(status==PCM_OK && pcm->platform->bind_fuel_ram_owners)
        (void)pcm_fuel_ram_owner_write8(pcm,address,value);
    return status;
}
