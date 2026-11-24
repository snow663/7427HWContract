#include "fuel_ram_owners.h"
/* Atomic canonical word publication, not a target hardware write. */
bool pcm_fuel_ram_owner_write16(Pcm *pcm,uint16_t address,uint16_t value)
{
    if(pcm==NULL)return false;
    switch(address) {
    case 0x00fd:pcm->scheduler.run_counter=value;return true;
    case 0x024c:pcm->reference.delivered_pulse=value;return true;
    case 0x027e:pcm->system.fuel_ignition_counter=value;return true;
    case 0x01d2:pcm->fuel.oxygen_filtered=value;return true;
    case 0x0284:
        pcm->spark.vehicle_speed_high=(uint8_t)(value>>8);
        pcm->io.vehicle_speed_fraction=(uint8_t)value;
        return true;
    case 0x080f:pcm->io.vss_previous=value;return true;
    case 0x0812:pcm->io.vss_raw=value;return true;
    default:return false;
    }
}
