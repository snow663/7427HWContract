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
    case 0x0063:pcm->spark.rpm_high=(uint8_t)(value>>8);pcm->spark.rpm_fraction=(uint8_t)value;return true;
    case 0x0068:pcm->reference.load_filtered=value;return true;
    case 0x006a:pcm->reference.load_event=value;return true;
    case 0x01ee:pcm->spark.command=value;return true;
    case 0x01f0:pcm->spark.command_latched=value;return true;
    case 0x01fd:pcm->spark.composite=value;return true;
    case 0x024e:pcm->fuel.corrected_pulse=value;return true;
    case 0x0250:pcm->reference.timer_pulse=value;return true;
    case 0x0254:pcm->reference.running_packet=value;return true;
    case 0x02cf:pcm->reference.crank_seed=value;return true;
    case 0x0818:pcm->fuel.pe_vehicle_change=value;return true;
    case 0x0851:pcm->fuel.authorization_capture=value;return true;
    case 0x088b:pcm->iac.airflow=value;return true;
    default:return false;
    }
}
