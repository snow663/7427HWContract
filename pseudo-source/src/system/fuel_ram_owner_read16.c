#include "fuel_ram_owners.h"
/* Big-endian $7D4B prefix word ownership. */
bool pcm_fuel_ram_owner_read16(const Pcm *pcm,uint16_t address,uint16_t *out)
{
    if(pcm==NULL||out==NULL)return false;
    switch(address) {
    case 0x00fd:*out=pcm->scheduler.run_counter;return true;
    case 0x024c:*out=pcm->reference.delivered_pulse;return true;
    case 0x027e:*out=pcm->system.fuel_ignition_counter;return true;
    case 0x01d2:*out=pcm->fuel.oxygen_filtered;return true;
    case 0x0284:
        *out=(uint16_t)(((uint16_t)pcm->spark.vehicle_speed_high<<8)|
                        pcm->io.vehicle_speed_fraction);return true;
    case 0x080f:*out=pcm->io.vss_previous;return true;
    case 0x0812:*out=pcm->io.vss_raw;return true;
    default:return false;
    }
}
