#include "fuel_ram_owners.h"
/* Reconstitute only source-owned flag bits over provider residual. */
static uint8_t with_bit(uint8_t byte,uint8_t mask,bool on)
{
    return on?(uint8_t)(byte|mask):(uint8_t)(byte&~mask);
}
#define BIT(b,mask,expr) ((b)=with_bit((b),(mask),(expr)))

bool pcm_fuel_ram_owner_read8(const Pcm *pcm,uint16_t address,uint8_t residual,uint8_t *out)
{
    if(pcm==NULL||out==NULL)return false;
    uint16_t word=0;
    uint8_t b=residual;
    switch(address) {
    case 0x0000:
        b=(uint8_t)(pcm->system.interrupt_flags&0xfeu);
        BIT(b,0x01u,pcm->scheduler.timer_seen);break;
    case 0x0002:b=pcm->scheduler.phase;break;
    case 0x0003:b=pcm->scheduler.busy_phase;break;
    case 0x0007:b=pcm->iac.position;break;
    case 0x0008:b=pcm->iac.target;break;
    case 0x000a:b=pcm->iac.step_control;break;
    case 0x003a:
        b&=(uint8_t)~0x6fu;
        BIT(b,0x01u,pcm->runtime.adc_fault);
        BIT(b,0x02u,pcm->system.rom_failure);
        BIT(b,0x04u,pcm->system.configuration_failure);
        BIT(b,0x08u,pcm->system.stack_recovery);
        BIT(b,0x20u,pcm->scheduler.pending);
        BIT(b,0x40u,pcm->system.adaptive_failure);
        break;
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
    case 0x004b:
        b=(uint8_t)(pcm->io.output_context&0x6fu);
        BIT(b,0x10u,pcm->spark.output_request);
        BIT(b,0x80u,pcm->iac.kicker_request);
        break;
    case 0x004c:b=pcm->transmission.output_shadow;break;
    case 0x004d:b=pcm->iac.input_shadow;break;
    case 0x004e:b=pcm->io.auxiliary_output;break;
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
        b=0;
        BIT(b,0x80u,pcm->spark.idle_state);
        BIT(b,0x40u,pcm->spark.idle_feedback);
        BIT(b,0x20u,pcm->reference.pending);
        BIT(b,0x10u,pcm->runtime.diagnostic_switch);
        BIT(b,0x08u,pcm->io.diagnostic_warm);
        BIT(b,0x04u,pcm->reference.consumed);
        BIT(b,0x02u,pcm->fuel.idle_afr_ready);
        BIT(b,0x01u,pcm->reference.sample_map);
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
    case 0x0811:b=pcm->io.vss_age;break;
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
    case 0x0284:case 0x0285:
        (void)pcm_fuel_ram_owner_read16(pcm,0x0284,&word);
        b=address==0x0284?(uint8_t)(word>>8):(uint8_t)word;break;
    case 0x080f:case 0x0810:
        (void)pcm_fuel_ram_owner_read16(pcm,0x080f,&word);
        b=address==0x080f?(uint8_t)(word>>8):(uint8_t)word;break;
    case 0x0812:case 0x0813:
        (void)pcm_fuel_ram_owner_read16(pcm,0x0812,&word);
        b=address==0x0812?(uint8_t)(word>>8):(uint8_t)word;break;
    case 0x0063:case 0x0064:
        (void)pcm_fuel_ram_owner_read16(pcm,0x0063,&word);
        b=address==0x0063?(uint8_t)(word>>8):(uint8_t)word;break;
    case 0x0068:case 0x0069:
        (void)pcm_fuel_ram_owner_read16(pcm,0x0068,&word);
        b=address==0x0068?(uint8_t)(word>>8):(uint8_t)word;break;
    case 0x006a:case 0x006b:
        (void)pcm_fuel_ram_owner_read16(pcm,0x006a,&word);
        b=address==0x006a?(uint8_t)(word>>8):(uint8_t)word;break;
    case 0x01ee:case 0x01ef:
        (void)pcm_fuel_ram_owner_read16(pcm,0x01ee,&word);
        b=address==0x01ee?(uint8_t)(word>>8):(uint8_t)word;break;
    case 0x01f0:case 0x01f1:
        (void)pcm_fuel_ram_owner_read16(pcm,0x01f0,&word);
        b=address==0x01f0?(uint8_t)(word>>8):(uint8_t)word;break;
    case 0x01fd:case 0x01fe:
        (void)pcm_fuel_ram_owner_read16(pcm,0x01fd,&word);
        b=address==0x01fd?(uint8_t)(word>>8):(uint8_t)word;break;
    case 0x024e:case 0x024f:
        (void)pcm_fuel_ram_owner_read16(pcm,0x024e,&word);
        b=address==0x024e?(uint8_t)(word>>8):(uint8_t)word;break;
    case 0x0250:case 0x0251:
        (void)pcm_fuel_ram_owner_read16(pcm,0x0250,&word);
        b=address==0x0250?(uint8_t)(word>>8):(uint8_t)word;break;
    case 0x0254:case 0x0255:
        (void)pcm_fuel_ram_owner_read16(pcm,0x0254,&word);
        b=address==0x0254?(uint8_t)(word>>8):(uint8_t)word;break;
    case 0x02cf:case 0x02d0:
        (void)pcm_fuel_ram_owner_read16(pcm,0x02cf,&word);
        b=address==0x02cf?(uint8_t)(word>>8):(uint8_t)word;break;
    case 0x0818:case 0x0819:
        (void)pcm_fuel_ram_owner_read16(pcm,0x0818,&word);
        b=address==0x0818?(uint8_t)(word>>8):(uint8_t)word;break;
    case 0x0851:case 0x0852:
        (void)pcm_fuel_ram_owner_read16(pcm,0x0851,&word);
        b=address==0x0851?(uint8_t)(word>>8):(uint8_t)word;break;
    case 0x088b:case 0x088c:
        (void)pcm_fuel_ram_owner_read16(pcm,0x088b,&word);
        b=address==0x088b?(uint8_t)(word>>8):(uint8_t)word;break;
    default:return false;
    }
    *out=b;
    return true;
}

#undef BIT
