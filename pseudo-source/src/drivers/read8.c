#include "pcm.h"
#include "fuel_ram_owners.h"
/* Preserve one physical-width source transaction, then resolve any
 * explicitly owned fuel-prefix RAM bit(s) from canonical C state.
 * The provider supplies unowned bits; a failed read never samples state. */
PcmStatus pcm_read8(Pcm *pcm,uint16_t address,uint8_t *value)
{
    if(pcm->platform==NULL || pcm->platform->read8==NULL)return PCM_NO_HARDWARE;
    PcmStatus status=pcm->platform->read8(pcm->platform->context,address,value);
    if(status!=PCM_OK || !pcm->platform->bind_fuel_ram_owners)return status;
    uint8_t canonical;
    if(pcm_fuel_ram_owner_read8(pcm,address,*value,&canonical))*value=canonical;
    return PCM_OK;
}
