#include "fuel_ram_owners.h"
#include "../serial/serial_internal.h"
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
    case 0x0063:*out=(uint16_t)(((uint16_t)pcm->spark.rpm_high<<8)|pcm->spark.rpm_fraction);return true;
    case 0x0068:*out=pcm->reference.load_filtered;return true;
    case 0x006a:*out=pcm->reference.load_event;return true;
    case 0x01ee:*out=pcm->spark.command;return true;
    case 0x01f0:*out=pcm->spark.command_latched;return true;
    case 0x01fd:*out=pcm->spark.composite;return true;
    case 0x024e:*out=pcm->fuel.corrected_pulse;return true;
    case 0x0250:*out=pcm->reference.timer_pulse;return true;
    case 0x0254:*out=pcm->reference.running_packet;return true;
    case 0x02cf:*out=pcm->reference.crank_seed;return true;
    case 0x0818:*out=pcm->fuel.pe_vehicle_change;return true;
    case 0x0851:*out=pcm->fuel.authorization_capture;return true;
    case 0x088b:*out=pcm->iac.airflow;return true;
    case 0x0234:*out=pcm->fuel.air_charge;return true;
    case 0x0238:*out=pcm->fuel.displaced;return true;
    case 0x023a:*out=pcm->fuel.acceleration_reservoir;return true;
    case 0x0252:*out=pcm->fuel.egr_subtract;return true;
    case 0x025a:*out=pcm->fuel.async_accumulator_fraction;return true;
    case 0x025c:*out=pcm->fuel.async_quotient;return true;
    case 0x081f:*out=pcm->reference.timer_delay;return true;
    default: {
        uint8_t high, low;
        if (address != 0xffffu && ser_get(pcm,address,&high) &&
            ser_get(pcm,(uint16_t)(address+1u),&low)) {
            *out=(uint16_t)(((uint16_t)high<<8)|low);
            return true;
        }
        return false;
    }
    }
}
