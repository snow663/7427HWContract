#include "fuel_ram_owners.h"
#include "../serial/serial_internal.h"
/* Apply only source-owned flags after a successful backing write. */
#define OWNED_BOOL(field,mask) do { (field)=((value&(mask))!=0); } while(0)
bool pcm_fuel_ram_owner_write8(Pcm *pcm,uint16_t address,uint8_t value)
{
    if(pcm==NULL)return false;
    uint16_t word;
    switch(address) {
    case 0x0000:
        pcm->system.interrupt_flags=(uint8_t)(value&0xfeu);
        OWNED_BOOL(pcm->scheduler.timer_seen,0x01u);return true;
    case 0x0002:pcm->scheduler.phase=value;return true;
    case 0x0003:pcm->scheduler.busy_phase=value;return true;
    case 0x0007:pcm->iac.position=value;return true;
    case 0x0008:pcm->iac.target=value;return true;
    case 0x000a:pcm->iac.step_control=value;return true;
    case 0x003a:
        OWNED_BOOL(pcm->runtime.adc_fault,0x01u);
        OWNED_BOOL(pcm->system.rom_failure,0x02u);
        OWNED_BOOL(pcm->system.configuration_failure,0x04u);
        OWNED_BOOL(pcm->system.stack_recovery,0x08u);
        OWNED_BOOL(pcm->scheduler.pending,0x20u);
        OWNED_BOOL(pcm->system.adaptive_failure,0x40u);return true;
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
    case 0x004b:
        pcm->io.output_context=(uint8_t)(value&0x6fu);
        OWNED_BOOL(pcm->spark.output_request,0x10u);
        OWNED_BOOL(pcm->iac.kicker_request,0x80u);return true;
    case 0x004c:pcm->transmission.output_shadow=value;return true;
    case 0x004d:pcm->iac.input_shadow=value;return true;
    case 0x004e:pcm->io.auxiliary_output=value;return true;
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
        OWNED_BOOL(pcm->spark.idle_feedback,0x40u);
        OWNED_BOOL(pcm->reference.pending,0x20u);
        OWNED_BOOL(pcm->runtime.diagnostic_switch,0x10u);
        OWNED_BOOL(pcm->io.diagnostic_warm,0x08u);
        OWNED_BOOL(pcm->reference.consumed,0x04u);
        OWNED_BOOL(pcm->fuel.idle_afr_ready,0x02u);
        OWNED_BOOL(pcm->reference.sample_map,0x01u);return true;
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
    case 0x0811:pcm->io.vss_age=value;return true;
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
    case 0x0284:case 0x0285:
        word=(uint16_t)(((uint16_t)pcm->spark.vehicle_speed_high<<8)|
                        pcm->io.vehicle_speed_fraction);
        word=address==0x0284?(uint16_t)(((uint16_t)value<<8)|(word&255u)):
                (uint16_t)((word&0xff00u)|value);
        return pcm_fuel_ram_owner_write16(pcm,0x0284,word);
    case 0x080f:case 0x0810:
        word=pcm->io.vss_previous;
        word=address==0x080f?(uint16_t)(((uint16_t)value<<8)|(word&255u)):
                (uint16_t)((word&0xff00u)|value);
        return pcm_fuel_ram_owner_write16(pcm,0x080f,word);
    case 0x0812:case 0x0813:
        word=pcm->io.vss_raw;
        word=address==0x0812?(uint16_t)(((uint16_t)value<<8)|(word&255u)):
                (uint16_t)((word&0xff00u)|value);
        return pcm_fuel_ram_owner_write16(pcm,0x0812,word);
    case 0x0063:case 0x0064:
        (void)pcm_fuel_ram_owner_read16(pcm,0x0063,&word);
        word=address==0x0063?(uint16_t)(((uint16_t)value<<8)|(word&255u)):
                (uint16_t)((word&0xff00u)|value);
        return pcm_fuel_ram_owner_write16(pcm,0x0063,word);
    case 0x0068:case 0x0069:
        (void)pcm_fuel_ram_owner_read16(pcm,0x0068,&word);
        word=address==0x0068?(uint16_t)(((uint16_t)value<<8)|(word&255u)):
                (uint16_t)((word&0xff00u)|value);
        return pcm_fuel_ram_owner_write16(pcm,0x0068,word);
    case 0x006a:case 0x006b:
        (void)pcm_fuel_ram_owner_read16(pcm,0x006a,&word);
        word=address==0x006a?(uint16_t)(((uint16_t)value<<8)|(word&255u)):
                (uint16_t)((word&0xff00u)|value);
        return pcm_fuel_ram_owner_write16(pcm,0x006a,word);
    case 0x01ee:case 0x01ef:
        (void)pcm_fuel_ram_owner_read16(pcm,0x01ee,&word);
        word=address==0x01ee?(uint16_t)(((uint16_t)value<<8)|(word&255u)):
                (uint16_t)((word&0xff00u)|value);
        return pcm_fuel_ram_owner_write16(pcm,0x01ee,word);
    case 0x01f0:case 0x01f1:
        (void)pcm_fuel_ram_owner_read16(pcm,0x01f0,&word);
        word=address==0x01f0?(uint16_t)(((uint16_t)value<<8)|(word&255u)):
                (uint16_t)((word&0xff00u)|value);
        return pcm_fuel_ram_owner_write16(pcm,0x01f0,word);
    case 0x01fd:case 0x01fe:
        (void)pcm_fuel_ram_owner_read16(pcm,0x01fd,&word);
        word=address==0x01fd?(uint16_t)(((uint16_t)value<<8)|(word&255u)):
                (uint16_t)((word&0xff00u)|value);
        return pcm_fuel_ram_owner_write16(pcm,0x01fd,word);
    case 0x024e:case 0x024f:
        (void)pcm_fuel_ram_owner_read16(pcm,0x024e,&word);
        word=address==0x024e?(uint16_t)(((uint16_t)value<<8)|(word&255u)):
                (uint16_t)((word&0xff00u)|value);
        return pcm_fuel_ram_owner_write16(pcm,0x024e,word);
    case 0x0250:case 0x0251:
        (void)pcm_fuel_ram_owner_read16(pcm,0x0250,&word);
        word=address==0x0250?(uint16_t)(((uint16_t)value<<8)|(word&255u)):
                (uint16_t)((word&0xff00u)|value);
        return pcm_fuel_ram_owner_write16(pcm,0x0250,word);
    case 0x0254:case 0x0255:
        (void)pcm_fuel_ram_owner_read16(pcm,0x0254,&word);
        word=address==0x0254?(uint16_t)(((uint16_t)value<<8)|(word&255u)):
                (uint16_t)((word&0xff00u)|value);
        return pcm_fuel_ram_owner_write16(pcm,0x0254,word);
    case 0x02cf:case 0x02d0:
        (void)pcm_fuel_ram_owner_read16(pcm,0x02cf,&word);
        word=address==0x02cf?(uint16_t)(((uint16_t)value<<8)|(word&255u)):
                (uint16_t)((word&0xff00u)|value);
        return pcm_fuel_ram_owner_write16(pcm,0x02cf,word);
    case 0x0818:case 0x0819:
        (void)pcm_fuel_ram_owner_read16(pcm,0x0818,&word);
        word=address==0x0818?(uint16_t)(((uint16_t)value<<8)|(word&255u)):
                (uint16_t)((word&0xff00u)|value);
        return pcm_fuel_ram_owner_write16(pcm,0x0818,word);
    case 0x0851:case 0x0852:
        (void)pcm_fuel_ram_owner_read16(pcm,0x0851,&word);
        word=address==0x0851?(uint16_t)(((uint16_t)value<<8)|(word&255u)):
                (uint16_t)((word&0xff00u)|value);
        return pcm_fuel_ram_owner_write16(pcm,0x0851,word);
    case 0x088b:case 0x088c:
        (void)pcm_fuel_ram_owner_read16(pcm,0x088b,&word);
        word=address==0x088b?(uint16_t)(((uint16_t)value<<8)|(word&255u)):
                (uint16_t)((word&0xff00u)|value);
        return pcm_fuel_ram_owner_write16(pcm,0x088b,word);
    default:return ser_put(pcm,address,value);
    }
}

#undef OWNED_BOOL
