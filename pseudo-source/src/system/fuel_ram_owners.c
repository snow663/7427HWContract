#include "fuel_ram_owners.h"

/* Sparse canonical ownership table. Shared bytes are reconstructed by
 * replacing ONLY model-owned bits; the caller supplies the remaining
 * provider value. Byte writes update every recognized owner after the
 * backing provider has accepted the exact stock write transaction. */
static uint8_t with_bit(uint8_t byte,uint8_t mask,bool on)
{
    return on?(uint8_t)(byte|mask):(uint8_t)(byte&~mask);
}
#define BIT(b,mask,expr) ((b)=with_bit((b),(mask),(expr)))
#define OWNED_BOOL(field,mask) do { (field)=((value&(mask))!=0); } while(0)

bool pcm_fuel_ram_owner_read16(const Pcm *pcm,uint16_t address,uint16_t *out)
{
    if(pcm==NULL||out==NULL)return false;
    switch(address) {
    case 0x00fd:*out=pcm->scheduler.run_counter;return true;
    case 0x024c:*out=pcm->reference.delivered_pulse;return true;
    case 0x027e:*out=pcm->system.fuel_ignition_counter;return true;
    case 0x01d2:*out=pcm->fuel.oxygen_filtered;return true;
    default:return false;
    }
}
bool pcm_fuel_ram_owner_write16(Pcm *pcm,uint16_t address,uint16_t value)
{
    if(pcm==NULL)return false;
    switch(address) {
    case 0x00fd:pcm->scheduler.run_counter=value;return true;
    case 0x024c:pcm->reference.delivered_pulse=value;return true;
    case 0x027e:pcm->system.fuel_ignition_counter=value;return true;
    case 0x01d2:pcm->fuel.oxygen_filtered=value;return true;
    default:return false;
    }
}
bool pcm_fuel_ram_owner_read8(const Pcm *pcm,uint16_t address,uint8_t residual,uint8_t *out)
{
    if(pcm==NULL||out==NULL)return false;
    uint16_t word=0;
    uint8_t b=residual;
    switch(address) {
    case 0x0004:
        b&=(uint8_t)~0x9fu;
        BIT(b,0x80u,pcm->spark.bypass_supervision);
        BIT(b,0x10u,pcm->scheduler.clear_after_run_count);
        BIT(b,0x08u,pcm->spark.run_transition);
        BIT(b,0x04u,pcm->runtime.refresh_late);
        BIT(b,0x02u,pcm->fuel.oxygen_warmed);
        BIT(b,0x01u,pcm->fuel.oxygen_activity);
        break;
    case 0x0019:
        b&=(uint8_t)~0x7cu;
        BIT(b,0x40u,pcm->reference.bank_fault);
        BIT(b,0x20u,pcm->spark.est_fault);
        BIT(b,0x10u,pcm->knock.sensor_fault);
        BIT(b,0x08u,pcm->fuel.oxygen_fault_b);
        BIT(b,0x04u,pcm->fuel.oxygen_fault_a);
        break;
    case 0x003e:
        b=(uint8_t)(pcm->io.coolant_context&0xfbu);
        BIT(b,0x04u,pcm->iac.low_battery);
        break;
    case 0x0041:
        b&=(uint8_t)~0x38u;
        BIT(b,0x20u,pcm->iac.park_neutral);
        BIT(b,0x10u,pcm->io.ac_mirror);
        BIT(b,0x08u,pcm->fuel.ac_enrichment_seen);
        break;
    case 0x0044:
        b&=(uint8_t)~0xdfu;
        BIT(b,0x80u,pcm->spark.bypass_fault_latched);
        BIT(b,0x40u,pcm->spark.bypass_qualified);
        BIT(b,0x10u,pcm->reference.latch_inhibited);
        BIT(b,0x08u,pcm->spark.first_reference);
        BIT(b,0x04u,pcm->runtime.output_override);
        BIT(b,0x02u,pcm->fuel.fuel_activity);
        BIT(b,0x01u,pcm->runtime.factory_mode);
        break;
    case 0x0046:
        b&=(uint8_t)~0xdbu;
        BIT(b,0x80u,pcm->fuel.closed_seen);
        BIT(b,0x40u,pcm->fuel.blm_invalid);
        BIT(b,0x10u,pcm->fuel.cut_active);
        BIT(b,0x08u,pcm->runtime.deceleration_fuel_cut);
        BIT(b,0x02u,pcm->fuel.oxygen_error_positive);
        BIT(b,0x01u,pcm->fuel.async_suppressed);
        break;
    case 0x0047:
        b=(uint8_t)(pcm->io.map_context&0xfeu);
        BIT(b,0x01u,pcm->io.map_transient);
        break;
    case 0x004f:
        b&=(uint8_t)~0xfdu;
        BIT(b,0x80u,pcm->runtime.spark_running);
        BIT(b,0x40u,pcm->spark.startup_gain_enabled);
        BIT(b,0x20u,pcm->fuel.ve_reset_request);
        BIT(b,0x10u,pcm->runtime.fuel_running);
        BIT(b,0x08u,pcm->fuel.open_ve);
        BIT(b,0x04u,pcm->scheduler.busy);
        BIT(b,0x01u,pcm->spark.command_negative);
        break;
    case 0x0050:
        b&=(uint8_t)~0x8au;
        BIT(b,0x80u,pcm->spark.idle_state);
        BIT(b,0x08u,pcm->io.diagnostic_warm);
        BIT(b,0x02u,pcm->fuel.idle_afr_ready);
        break;
    case 0x0051:
        b&=(uint8_t)~0xedu;
        BIT(b,0x80u,pcm->reference.bank_latch);
        BIT(b,0x40u,pcm->spark.startup_gain_complete);
        BIT(b,0x20u,pcm->spark.recovery_active);
        BIT(b,0x08u,pcm->runtime.ignition_off);
        BIT(b,0x04u,pcm->runtime.refresh_requested);
        BIT(b,0x01u,pcm->reference.packet_updated);
        break;
    case 0x0086:
        b&=(uint8_t)~0x49u;
        BIT(b,0x40u,pcm->scheduler.profiling_enabled);
        BIT(b,0x08u,pcm->system.retained_initialized);
        BIT(b,0x01u,pcm->transmission.driver_inhibit);
        break;
    case 0x0062:b=pcm->reference.rpm_coordinate;break;
    case 0x0063:b=pcm->spark.rpm_high;break;
    case 0x0065:b=pcm->io.map_previous_rpm;break;
    case 0x0089:b=pcm->transmission.range_context;break;
    case 0x01c5:b=pcm->io.map_hold;break;
    case 0x01c6:b=pcm->spark.map_filtered;break;
    case 0x01d5:b=pcm->fuel.raw_oxygen;break;
    case 0x01d9:b=pcm->reference.throttle;break;
    case 0x0223:b=pcm->io.egr_failure_count;break;
    case 0x0268:b=pcm->reference.enrichment_age;break;
    case 0x027b:b=pcm->fuel.oxygen_coordinate;break;
    case 0x027d:b=pcm->fuel.startup_park_hold;break;
    case 0x02cd:b=pcm->reference.crank_references;break;
    case 0x02ce:b=pcm->reference.event_age;break;
    case 0x0299:b=pcm->transmission.governor_requested_throttle;break;
    case 0x00fd:case 0x00fe:
        (void)pcm_fuel_ram_owner_read16(pcm,0x00fd,&word);
        b=address==0x00fd?(uint8_t)(word>>8):(uint8_t)word;break;
    case 0x024c:case 0x024d:
        (void)pcm_fuel_ram_owner_read16(pcm,0x024c,&word);
        b=address==0x024c?(uint8_t)(word>>8):(uint8_t)word;break;
    case 0x027e:case 0x027f:
        (void)pcm_fuel_ram_owner_read16(pcm,0x027e,&word);
        b=address==0x027e?(uint8_t)(word>>8):(uint8_t)word;break;
    case 0x01d2:case 0x01d3:
        (void)pcm_fuel_ram_owner_read16(pcm,0x01d2,&word);
        b=address==0x01d2?(uint8_t)(word>>8):(uint8_t)word;break;
    default:return false;
    }
    *out=b;
    return true;
}
bool pcm_fuel_ram_owner_write8(Pcm *pcm,uint16_t address,uint8_t value)
{
    if(pcm==NULL)return false;
    uint16_t word;
    switch(address) {
    case 0x0004:
        OWNED_BOOL(pcm->spark.bypass_supervision,0x80u);
        OWNED_BOOL(pcm->scheduler.clear_after_run_count,0x10u);
        OWNED_BOOL(pcm->spark.run_transition,0x08u);
        OWNED_BOOL(pcm->runtime.refresh_late,0x04u);
        OWNED_BOOL(pcm->fuel.oxygen_warmed,0x02u);
        OWNED_BOOL(pcm->fuel.oxygen_activity,0x01u);
        return true;
    case 0x0019:
        OWNED_BOOL(pcm->reference.bank_fault,0x40u);
        OWNED_BOOL(pcm->spark.est_fault,0x20u);
        OWNED_BOOL(pcm->knock.sensor_fault,0x10u);
        OWNED_BOOL(pcm->fuel.oxygen_fault_b,0x08u);
        OWNED_BOOL(pcm->fuel.oxygen_fault_a,0x04u);
        return true;
    case 0x003e:
        pcm->io.coolant_context=(uint8_t)(value&0xfbu);
        OWNED_BOOL(pcm->iac.low_battery,0x04u);return true;
    case 0x0041:
        OWNED_BOOL(pcm->iac.park_neutral,0x20u);
        OWNED_BOOL(pcm->io.ac_mirror,0x10u);
        OWNED_BOOL(pcm->fuel.ac_enrichment_seen,0x08u);return true;
    case 0x0044:
        OWNED_BOOL(pcm->spark.bypass_fault_latched,0x80u);
        OWNED_BOOL(pcm->spark.bypass_qualified,0x40u);
        OWNED_BOOL(pcm->reference.latch_inhibited,0x10u);
        OWNED_BOOL(pcm->spark.first_reference,0x08u);
        OWNED_BOOL(pcm->runtime.output_override,0x04u);
        OWNED_BOOL(pcm->fuel.fuel_activity,0x02u);
        OWNED_BOOL(pcm->runtime.factory_mode,0x01u);return true;
    case 0x0046:
        OWNED_BOOL(pcm->fuel.closed_seen,0x80u);
        OWNED_BOOL(pcm->fuel.blm_invalid,0x40u);
        OWNED_BOOL(pcm->fuel.cut_active,0x10u);
        OWNED_BOOL(pcm->runtime.deceleration_fuel_cut,0x08u);
        OWNED_BOOL(pcm->fuel.oxygen_error_positive,0x02u);
        OWNED_BOOL(pcm->fuel.async_suppressed,0x01u);return true;
    case 0x0047:
        pcm->io.map_context=(uint8_t)(value&0xfeu);
        OWNED_BOOL(pcm->io.map_transient,0x01u);return true;
    case 0x004f:
        OWNED_BOOL(pcm->runtime.spark_running,0x80u);
        OWNED_BOOL(pcm->spark.startup_gain_enabled,0x40u);
        OWNED_BOOL(pcm->fuel.ve_reset_request,0x20u);
        OWNED_BOOL(pcm->runtime.fuel_running,0x10u);
        OWNED_BOOL(pcm->fuel.open_ve,0x08u);
        OWNED_BOOL(pcm->scheduler.busy,0x04u);
        OWNED_BOOL(pcm->spark.command_negative,0x01u);return true;
    case 0x0050:
        OWNED_BOOL(pcm->spark.idle_state,0x80u);
        OWNED_BOOL(pcm->io.diagnostic_warm,0x08u);
        OWNED_BOOL(pcm->fuel.idle_afr_ready,0x02u);return true;
    case 0x0051:
        OWNED_BOOL(pcm->reference.bank_latch,0x80u);
        OWNED_BOOL(pcm->spark.startup_gain_complete,0x40u);
        OWNED_BOOL(pcm->spark.recovery_active,0x20u);
        OWNED_BOOL(pcm->runtime.ignition_off,0x08u);
        OWNED_BOOL(pcm->runtime.refresh_requested,0x04u);
        OWNED_BOOL(pcm->reference.packet_updated,0x01u);return true;
    case 0x0086:
        OWNED_BOOL(pcm->scheduler.profiling_enabled,0x40u);
        OWNED_BOOL(pcm->system.retained_initialized,0x08u);
        OWNED_BOOL(pcm->transmission.driver_inhibit,0x01u);return true;
    case 0x0062:pcm->reference.rpm_coordinate=value;return true;
    case 0x0063:pcm->spark.rpm_high=value;return true;
    case 0x0065:pcm->io.map_previous_rpm=value;return true;
    case 0x0089:pcm->transmission.range_context=value;return true;
    case 0x01c5:pcm->io.map_hold=value;return true;
    case 0x01c6:pcm->spark.map_filtered=value;return true;
    case 0x01d5:pcm->fuel.raw_oxygen=value;return true;
    case 0x01d9:pcm->reference.throttle=value;return true;
    case 0x0223:pcm->io.egr_failure_count=value;return true;
    case 0x0268:pcm->reference.enrichment_age=value;return true;
    case 0x027b:pcm->fuel.oxygen_coordinate=value;return true;
    case 0x027d:pcm->fuel.startup_park_hold=value;return true;
    case 0x02cd:pcm->reference.crank_references=value;return true;
    case 0x02ce:pcm->reference.event_age=value;return true;
    case 0x0299:pcm->transmission.governor_requested_throttle=value;return true;
    case 0x00fd:case 0x00fe:
        word=pcm->scheduler.run_counter;
        word=address==0x00fd?(uint16_t)(((uint16_t)value<<8)|(word&255u)):
                (uint16_t)((word&0xff00u)|value);
        return pcm_fuel_ram_owner_write16(pcm,0x00fd,word);
    case 0x024c:case 0x024d:
        word=pcm->reference.delivered_pulse;
        word=address==0x024c?(uint16_t)(((uint16_t)value<<8)|(word&255u)):
                (uint16_t)((word&0xff00u)|value);
        return pcm_fuel_ram_owner_write16(pcm,0x024c,word);
    case 0x027e:case 0x027f:
        word=pcm->system.fuel_ignition_counter;
        word=address==0x027e?(uint16_t)(((uint16_t)value<<8)|(word&255u)):
                (uint16_t)((word&0xff00u)|value);
        return pcm_fuel_ram_owner_write16(pcm,0x027e,word);
    case 0x01d2:case 0x01d3:
        word=pcm->fuel.oxygen_filtered;
        word=address==0x01d2?(uint16_t)(((uint16_t)value<<8)|(word&255u)):
                (uint16_t)((word&0xff00u)|value);
        return pcm_fuel_ram_owner_write16(pcm,0x01d2,word);
    default:return false;
    }
}
#undef OWNED_BOOL
#undef BIT
