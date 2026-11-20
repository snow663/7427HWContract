#include "pcm.h"
#include "fuel_ram_owners.h"
/* Word callbacks remain word-width operations. The opt-in RAM map
 * exposes canonical values for mapped RAM, not guessed board registers. */
PcmStatus pcm_read16(Pcm *pcm,uint16_t address,uint16_t *value)
{
    if(pcm->platform==NULL || pcm->platform->read16==NULL)return PCM_NO_HARDWARE;
    PcmStatus status=pcm->platform->read16(pcm->platform->context,address,value);
    if(status!=PCM_OK || !pcm->platform->bind_fuel_ram_owners)return status;
    uint16_t canonical;
    if(pcm_fuel_ram_owner_read16(pcm,address,&canonical))*value=canonical;
    return PCM_OK;
}
