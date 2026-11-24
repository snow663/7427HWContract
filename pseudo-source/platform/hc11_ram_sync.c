#include "hc11_ram_sync.h"
#include "fuel_ram_owners.h"

/* Deliberately internal RAM only. One physical owner of the external GEN,
 * EEPROM or peripheral address space is not yet established on this board.
 * No write to external output registers can pass this gate. */
static bool internal_range(uint16_t address,uint8_t width)
{
    return width == 1u ? address <= 0x03ffu :
           width == 2u ? address <  0x03ffu : false;
}

/* The existing read adapter has a strict residual-bit contract. Probe with
 * 0 and FF to determine which bit positions are independent of residual
 * backing. No duplicate per-field ownership table is maintained.
 * Unmapped addresses return false rather than being guessed. */
static bool byte_owned_mask(const Pcm *pcm,uint16_t address,uint8_t *mask)
{
    uint8_t a,b;
    if(!pcm_fuel_ram_owner_read8(pcm,address,0u,&a) ||
       !pcm_fuel_ram_owner_read8(pcm,address,0xffu,&b))return false;
    *mask=(uint8_t)~(a^b);
    return *mask!=0u;
}

static PcmStatus verify(const PcmRamSyncGuard *guard)
{
    return guard->verify_exclusive(guard->context);
}

PcmStatus pcm_ram_sync_publish(Pcm *pcm, const PcmRamSyncEntry *entries,
                               size_t count, const PcmRamSyncGuard *guard,
                               PcmRamSyncReport *report)
{
    if(report==NULL)return PCM_BAD_CONFIGURATION;
    *report=(PcmRamSyncReport){0,0,0,count};
    if(pcm==NULL||pcm->platform==NULL||entries==NULL||count==0u||
       guard==NULL||guard->verify_exclusive==NULL)
        return PCM_BAD_CONFIGURATION;
    PcmPlatform *platform=pcm->platform;
    if(!platform->bind_fuel_ram_owners)
        return PCM_BAD_CONFIGURATION;
    if(platform->read8==NULL||platform->write8==NULL||
       platform->read16==NULL||platform->write16==NULL)
        return PCM_NO_HARDWARE;
    /* Ownership probing itself reads live C fields. The caller's exclusive
     * boundary must be established BEFORE validating even the first owner. */
    PcmStatus initial=verify(guard);
    if(initial!=PCM_OK){report->failed_index=0;return initial;}

    /* Fully reject malformed/overlapping/unsupported ownership requests
     * BEFORE attempting a read or publishing any RAM byte. */
    uint32_t prior_end=0u;
    for(size_t i=0;i<count;++i) {
        const PcmRamSyncEntry *e=&entries[i];
        if(!internal_range(e->address,e->width))
            return PCM_NO_HARDWARE;
        if(i>0 && (uint32_t)e->address<=prior_end)
            return PCM_BAD_CONFIGURATION;
        prior_end=(uint32_t)e->address+e->width-1u;
        if(e->width==1u) {
            uint8_t owned;
            if(e->mask==0u||e->mask>0xffu||
               !byte_owned_mask(pcm,e->address,&owned)||
               (e->mask&~(uint16_t)owned)!=0u)
                return PCM_BAD_CONFIGURATION;
        } else {
            uint16_t ignored;
            if(e->mask!=0xffffu||
               !pcm_fuel_ram_owner_read16(pcm,e->address,&ignored))
                return PCM_BAD_CONFIGURATION;
        }
    }

    for(size_t i=0;i<count;++i) {
        PcmStatus status=verify(guard);
        if(status!=PCM_OK){report->failed_index=i;return status;}
        const PcmRamSyncEntry *e=&entries[i];
        if(e->width==1u) {
            uint8_t physical,owned;
            ++report->examined;
            status=platform->read8(platform->context,e->address,&physical);
            if(status!=PCM_OK){report->failed_index=i;return status;}
            if(!pcm_fuel_ram_owner_read8(pcm,e->address,physical,&owned)){
                report->failed_index=i;return PCM_BAD_CONFIGURATION;
            }
            uint8_t wanted=(uint8_t)((physical&(uint8_t)~e->mask) |
                                      (owned&(uint8_t)e->mask));
            if(wanted==physical){++report->already_equal;continue;}
            status=verify(guard);
            if(status!=PCM_OK){report->failed_index=i;return status;}
            status=platform->write8(platform->context,e->address,wanted);
        } else {
            uint16_t physical,owned;
            ++report->examined;
            status=platform->read16(platform->context,e->address,&physical);
            if(status!=PCM_OK){report->failed_index=i;return status;}
            if(!pcm_fuel_ram_owner_read16(pcm,e->address,&owned)){
                report->failed_index=i;return PCM_BAD_CONFIGURATION;
            }
            if(owned==physical){++report->already_equal;continue;}
            status=verify(guard);
            if(status!=PCM_OK){report->failed_index=i;return status;}
            status=platform->write16(platform->context,e->address,owned);
        }
        if(status!=PCM_OK){report->failed_index=i;return status;}
        ++report->written;
    }
    return PCM_OK;
}
