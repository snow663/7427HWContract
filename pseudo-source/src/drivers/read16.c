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
    if(pcm_fuel_ram_owner_read16(pcm,address,&canonical)) {
        *value=canonical;
        return PCM_OK;
    }
    /* A word may cross two different named byte owners: preserve the one
     * physical 16-bit transaction, then merge their C-state byte views
     * over the provider's independent high/low residuals. */
    uint8_t high=(uint8_t)(*value>>8),low=(uint8_t)*value,owned;
    if(pcm_fuel_ram_owner_read8(pcm,address,high,&owned))high=owned;
    if(address!=0xffffu &&
       pcm_fuel_ram_owner_read8(pcm,(uint16_t)(address+1u),low,&owned))
        low=owned;
    *value=(uint16_t)(((uint16_t)high<<8)|low);
    return PCM_OK;
}
