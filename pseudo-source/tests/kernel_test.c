#include "scheduler.h"
#include "hardware.h"
#include "control.h"
#include "calibration.h"
#include "fuel.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CHECK(x) do { if (!(x)) { fprintf(stderr,"Check failed at %s:%d: %s\n",__FILE__,__LINE__,#x); exit(1); } } while (0)
typedef struct {
    uint8_t memory[65536]; /* Test fixture only; never the target RAM model. */
    unsigned counts[PCM_TASK_COUNT];
    PcmTask trace[2048]; unsigned used;
    unsigned timer_writes, current_writes, watchdog_writes, adc_starts, spark_writes, period_reads;
    unsigned connection_action, signature_reads, transmission_writes;
    unsigned slot4_coolant_updates, slot4_transmission_updates;
    unsigned tcc_qualification_calls, purge_duty_writes, register_refreshes, purge_commands;
    unsigned egr_demand_writes, egr_fraction_writes, egr_output_writes, transmission_baro_writes, slot_f_diagnostic_writes;
    uint8_t step_positions[256], observed_shadows[256];
    unsigned step_observations, shadow_observations;
    bool masked, inject, injected, guard_fails, feed_reference, stack_capture_fail;
    uint16_t supplied_stack_x;
    unsigned stack_captures;
    Pcm *pcm;
    PcmPlatform platform;
} Fixture;
static PcmStatus read8(void *v, uint16_t a, uint8_t *out) {
    Fixture *f=v;*out=f->memory[a];
    if (a==0x006e) *out=(uint8_t)((*out&0x7fu)|(f->pcm->spark.egr_active?0x80u:0));
    if (a==0x01b2) *out=f->pcm->spark.egr_fraction_high;
    if (a==0x01b3) *out=f->pcm->fuel.egr_fraction_low;
    if (a==0x02f3) *out=f->pcm->io.barometric_sample;
    if (a==0x02f4) *out=f->pcm->spark.barometric_high;
    if (a==0x02f5) *out=f->pcm->io.barometric_fraction;
    if (a==0x1c) *out=f->pcm->transmission.fault_flags_primary;
    if (a==0x1d) *out=f->pcm->transmission.fault_flags_secondary;
    if (a==0x99) *out=f->pcm->transmission.inhibit_flags;
    if (a==0x89) *out=f->pcm->transmission.range_context;
    if (a==PCM_ADCTL) *out|=0x80; /* Explicit ready peripheral fixture. */
    return PCM_OK;
}
static PcmStatus read16(void *v, uint16_t a, uint16_t *out) {
    Fixture *f=v;
    if (a==PCM_REFERENCE_PERIOD) ++f->period_reads;
    if (a==PCM_EXTENSION_SIGNATURE) ++f->signature_reads;
    *out=(uint16_t)((uint16_t)f->memory[a]*256u+f->memory[(uint16_t)(a+1u)]);
    if (a==0x01b2) *out=(uint16_t)((uint16_t)f->pcm->spark.egr_fraction_high*256u+f->pcm->fuel.egr_fraction_low);
    if (a==0x02f4) *out=(uint16_t)((uint16_t)f->pcm->spark.barometric_high*256u+f->pcm->io.barometric_fraction);
    return PCM_OK;
}
static PcmStatus write8(void *v, uint16_t a, uint8_t value) {
    Fixture *f=v; f->memory[a]=value;
    if (a==0x01ae) ++f->egr_demand_writes;
    if (a==0x01d6 && (f->pcm->scheduler.phase & 15u)==10u) ++f->purge_duty_writes;
    if (a==PCM_CSGSIZ) ++f->register_refreshes;
    if (a==0x006e) f->pcm->spark.egr_active=(value&0x80u)!=0;
    if (a==0x01b2) f->pcm->spark.egr_fraction_high=value;
    if (a==0x01b3) f->pcm->fuel.egr_fraction_low=value;
    if (a==0x02f3) f->pcm->io.barometric_sample=value;
    if (a==0x02f4) f->pcm->spark.barometric_high=value;
    if (a==0x02f5) f->pcm->io.barometric_fraction=value;
    if (a==0x1c) f->pcm->transmission.fault_flags_primary=value;
    if (a==0x1d) f->pcm->transmission.fault_flags_secondary=value;
    if (a==0x99) f->pcm->transmission.inhibit_flags=value;
    if (a==0x89) f->pcm->transmission.range_context=value;
    if (a==0x166) ++f->slot_f_diagnostic_writes;
    /* The captured-X adapter binds the guard's shared RAM writes to their
     * canonical owners before the separate recovery continuation is entered. */
    if (f->platform.capture_timer_stack_x!=NULL) {
        if (a==0x004f) f->pcm->scheduler.busy=(value&4u)!=0;
        if (a==0x003a) {
            f->pcm->system.stack_recovery=(value&8u)!=0;
            f->pcm->scheduler.pending=(value&0x20u)!=0;
        }
    }
    if (a==PCM_ADCTL) {
        ++f->adc_starts;
        if (value==7) {
            CHECK(f->masked && f->step_observations<256);
            f->step_positions[f->step_observations++]=f->pcm->iac.position;
        }
    }
    if (a==PCM_COPRST) {
        CHECK(value==0xaa || value==0x55); ++f->watchdog_writes;
        if (value==0xaa && f->feed_reference) {
            f->pcm->reference.pending=true;f->pcm->knock.retard=13;
        }
    }
    if (a==PCM_REFERENCE_STROBE) {
        CHECK(f->shadow_observations<256 && f->masked);
        f->observed_shadows[f->shadow_observations++]=value;
    }
    return PCM_OK;
}
static PcmStatus write16(void *v, uint16_t a, uint16_t value) {
    Fixture *f=v; f->memory[a]=(uint8_t)(value>>8); f->memory[(uint16_t)(a+1u)]=(uint8_t)value;
    if (a==0x01b2) {
        ++f->egr_fraction_writes;
        f->pcm->spark.egr_fraction_high=(uint8_t)(value>>8);f->pcm->fuel.egr_fraction_low=(uint8_t)value;
    }
    if (a==0x3fd6) ++f->purge_commands;
    if (a==0x8c) ++f->tcc_qualification_calls;
    if (a==0xa9) ++f->slot4_coolant_updates;
    if (a==0xb5) ++f->slot4_transmission_updates;
    if (a==0x3fd8) ++f->egr_output_writes;
    if (a==0x00ac) ++f->transmission_baro_writes;
    if (a==0x02f4) {
        f->pcm->spark.barometric_high=(uint8_t)(value>>8);f->pcm->io.barometric_fraction=(uint8_t)value;
    }
    if (a==PCM_TOC3) ++f->timer_writes;
    if (a==PCM_CURRENT_COMMAND) ++f->current_writes;
    if (a==PCM_SPARK_TIMING_A) ++f->spark_writes;
    if (a==PCM_TCC_COMMAND) ++f->transmission_writes;
    return PCM_OK;
}
static PcmStatus mask_irq(void *v, bool value) {
    Fixture *f=v;f->masked=value;
    if (!value && f->inject && !f->injected && f->shadow_observations!=0) {
        f->injected=true;
        for (unsigned k=0;k<3;++k) CHECK(pcm_periodic_irq(f->pcm)==PCM_OK);
    }
    return PCM_OK;
}
static PcmStatus delay_cycles(void *v,uint16_t cycles) { (void)v;CHECK(cycles==11 || cycles==33);return PCM_OK; }
static PcmStatus guard(void *v, bool busy) {
    Fixture *f=v; (void)busy; return f->guard_fails?PCM_STACK_BOUNDARY:PCM_OK;
}
static PcmStatus capture_stack_x(void *v,uint16_t *sample)
{
    Fixture *f=v;++f->stack_captures;
    if (f->stack_capture_fail) return PCM_NO_HARDWARE;
    *sample=f->supplied_stack_x;return PCM_OK;
}
static PcmStatus task(Pcm *pcm, PcmTask id) {
    Fixture *f=pcm->platform->context;
    CHECK(f->used<sizeof(f->trace)/sizeof(f->trace[0]));
    f->trace[f->used++]=id; ++f->counts[id];
    if (id==PCM_SLOT_02) CHECK(f->masked);
    if (id==PCM_CONNECTION_EXTENSION && f->connection_action)
        pcm->scheduler.profiling_enabled=f->connection_action==1;
    return PCM_OK;
}
static void init(Fixture *f, Pcm *pcm) {
    memset(f,0,sizeof(*f)); memset(pcm,0,sizeof(*pcm));
    f->platform.context=f; f->platform.read8=read8; f->platform.read16=read16;
    f->platform.write8=write8; f->platform.write16=write16; f->platform.mask_irq=mask_irq;
    f->platform.check_stack=guard;
    f->platform.delay_cycles=delay_cycles;f->pcm=pcm;
    for (unsigned k=0;k<PCM_TASK_COUNT;++k) f->platform.task[k]=task;
    f->platform.task[PCM_IAC_CONTROL]=NULL;
    f->platform.task[PCM_IAC_STEP]=NULL;
    f->platform.task[PCM_ADC_FEEDBACK]=NULL;
    f->platform.task[PCM_CURRENT_CONTROL]=NULL;
    f->platform.task[PCM_SLOT_00]=f->platform.task[PCM_SLOT_02]=NULL;
    f->platform.task[PCM_SLOT_04]=NULL;
    f->platform.task[PCM_SLOT_05]=f->platform.task[PCM_SLOT_0A]=NULL;
    f->platform.task[PCM_SLOT_03]=f->platform.task[PCM_SLOT_0B]=NULL;
    f->platform.task[PCM_SLOT_0C]=f->platform.task[PCM_SLOT_0D]=NULL;
    f->platform.task[PCM_SLOT_0F]=NULL;
    f->platform.task[PCM_AC_SWITCH_INPUTS]=f->platform.task[PCM_SHIFT_LAMP]=f->platform.task[PCM_VSS_FILTER]=NULL;
    f->platform.task[PCM_COMMON_IO]=f->platform.task[PCM_INPUT_HOUSEKEEPING]=NULL;
    f->platform.task[PCM_SERIAL_POLL]=f->platform.task[PCM_SCI_BODY]=f->platform.task[PCM_RESET_SERIAL]=NULL;
    f->platform.task[PCM_TRANSMISSION_INPUT]=NULL;
    f->platform.task[PCM_RESET_RAM]=NULL;
    f->platform.task[PCM_RESET_SENSORS]=NULL;
    f->platform.task[PCM_RESET_RETAINED]=NULL;
    f->platform.task[PCM_RESET_CONTROLLERS]=NULL;
    pcm->platform=&f->platform; pcm->calibration=&pcm_reference_scheduler_calibration;
    pcm->scheduler.phase=0x0e;
    pcm->spark.battery_sample=130;
    pcm->io.diagnostic_sample=100;pcm->reference.map_sample=135;pcm->io.map_filter=0x8700;
    f->memory[PCM_ADR2]=135;f->memory[PCM_ADR4]=130; /* Stable nominal battery input. */
}
static void test_initialization_and_missing_contracts(void) {
    static Fixture f; Pcm pcm; init(&f,&pcm);
    f.memory[PCM_TCNT]=0xff; f.memory[PCM_TCNT+1]=0xfc;
    pcm.knock.sample_baseline=0xabcd; pcm.knock.observation_accumulator=0x55;
    pcm.knock.retard=0x23; pcm.knock.sensor_fault=true; pcm.knock.sensor_fault_count=0x64;
    pcm.spark.command=0xabcd; pcm.runtime.adc_timeout=true; pcm.runtime.adc_fault=true;
    pcm.transmission.output_shadow=0xff;pcm.transmission.tcc_command=0xabcd;
    pcm.iac.transfer_flags=0xff;pcm.iac.bank[0].cold=0xabcd;
    pcm.io.map_filter=0xabcd;pcm.io.auxiliary_output=0xff;
    CHECK(pcm_reset_sequence(&pcm,&f.platform,&pcm_reference_scheduler_calibration)==PCM_OK);
    CHECK(pcm.scheduler.phase==0x0e && !f.masked);
    CHECK(pcm.knock.sample_baseline==0 && pcm.knock.observation_accumulator==0);
    CHECK(pcm.knock.retard==0 && !pcm.knock.sensor_fault && pcm.knock.sensor_fault_count==0);
    CHECK(pcm.spark.command==0 && !pcm.runtime.adc_timeout && !pcm.runtime.adc_fault);
    CHECK(pcm.transmission.output_shadow==0x40 && pcm.transmission.tcc_command==0);
    CHECK(pcm.iac.transfer_flags==0 && pcm.iac.bank[0].cold==0);
    CHECK(pcm.io.map_filter==0 && pcm.io.auxiliary_output==0);
    CHECK(f.memory[PCM_TOC3]==0 && f.memory[PCM_TOC3+1]==4);
    CHECK(f.memory[PCM_TMSK1]==0xa0);
    CHECK(pcm.system.startup_counter==20 && pcm.iac.blm_value==128 && f.counts[PCM_RESET_SERIAL]==0);
    static const PcmTask expected[]={PCM_RESET_ENTRY};
    CHECK(f.used==sizeof(expected)/sizeof(expected[0]));
    CHECK(memcmp(f.trace,expected,sizeof(expected))==0);
    init(&f,&pcm);pcm.system.factory_flags=0xa5;
    f.memory[PCM_ADR1]=252;f.memory[PCM_ADR2]=64;f.memory[PCM_ADR3]=5;f.memory[PCM_ADR4]=252;
    CHECK(pcm_reset_sequence(&pcm,&f.platform,&pcm_reference_scheduler_calibration)==PCM_FACTORY_BOUNDARY);
    CHECK(pcm.runtime.factory_mode && pcm.io.diagnostic_warm && pcm.system.factory_flags==0 && !f.masked);
    CHECK(f.used==1 && f.trace[0]==PCM_RESET_ENTRY && f.timer_writes==0);
    CHECK(f.memory[PCM_BOARD_CONTROL]==0xb9 && f.memory[PCM_BOARD_CONTROL+1]==0x3a);
    init(&f,&pcm); f.platform.delay_cycles=NULL;
    CHECK(pcm_main_pass(&pcm)==PCM_NO_HARDWARE && f.counts[PCM_FUEL_CONTROL]==0);
    pcm.platform=NULL; CHECK(pcm_watchdog_service(&pcm)==PCM_NO_HARDWARE);
}
static void test_full_phase_cycle(void) {
    static Fixture f; Pcm pcm; init(&f,&pcm); pcm.scheduler.phase=0x9f;
    f.feed_reference=true;pcm.runtime.spark_running=pcm.runtime.fuel_running=true;
    pcm.reference.coolant=200;pcm.spark.load_coordinate=128;pcm.spark.previous_load=128;
    pcm.knock.retard=13;pcm.knock.activity=7;pcm.knock.learning_high=true;
    for (unsigned k=0;k<160;++k) {
        unsigned prior_writes=f.transmission_writes;
        unsigned prior_tcc=f.tcc_qualification_calls, prior_purge=f.purge_duty_writes;
        CHECK(pcm_periodic_irq(&pcm)==PCM_OK);
        CHECK(pcm.scheduler.phase==k && !pcm.scheduler.busy);
        CHECK(f.register_refreshes==(k+4)/16 && f.purge_commands==(k+3)/16);
        CHECK(f.tcc_qualification_calls==prior_tcc+(k%16u==5u));
        CHECK(f.purge_duty_writes==prior_purge+(k%32u==10u));
        CHECK(f.transmission_writes==prior_writes+(k%4u==3u)); /* slots 03, 07, 0B, 0F */
    }
    CHECK(f.counts[PCM_IAC_STEP]==0 && f.step_observations==160 && f.current_writes==160);
    CHECK(f.counts[PCM_COMMON_IO]==0 && f.counts[PCM_INPUT_HOUSEKEEPING]==0 && f.shadow_observations==160);
    CHECK(f.counts[PCM_SERIAL_POLL]==0);
    CHECK(f.watchdog_writes==160); /* Housekeeping AA and resident fuel55 on alternate phases. */
    CHECK(f.counts[PCM_SPARK_CONTROL]==0 && f.spark_writes==80 && f.counts[PCM_FUEL_CONTROL]==0);
    CHECK(f.counts[PCM_TRANSMISSION_INPUT]==0 && f.counts[PCM_TRANSMISSION_INPUT_PREFIX]==40 && f.counts[PCM_PRESSURE_TCC]==40);
    CHECK(f.counts[PCM_SHIFT_CONTROL]==40 && f.counts[PCM_IAC_CONTROL]==0);
    CHECK(pcm.iac.rpm_error!=0); /* Resident main IAC runs without its old task. */
    for (unsigned k=PCM_SLOT_00;k<=PCM_SLOT_0F;++k)
        CHECK(f.counts[k] == 0);
    CHECK(f.signature_reads==10 && f.transmission_writes==40 && f.counts[PCM_CONNECTION_EXTENSION]==0);
    CHECK(f.memory[0x0f00]==0xf7);
    CHECK(f.slot_f_diagnostic_writes==10);
    CHECK(f.slot4_coolant_updates==5 && f.slot4_transmission_updates==5);
    CHECK(f.counts[PCM_IAC_BACKGROUND]==0 && f.counts[PCM_SHIFT_LAMP]==0);
    CHECK(pcm.iac.slewed_base!=0 && pcm.iac.kicker_request);
    CHECK(f.counts[PCM_EGR_DEMAND]==0 && f.counts[PCM_EGR_FLOW]==0 && f.counts[PCM_VSS_FILTER]==0);
    CHECK(f.egr_demand_writes==10 && f.egr_fraction_writes==40 && f.egr_output_writes==80);
    CHECK(f.transmission_baro_writes==10 && f.counts[PCM_SLOT_01]==0);
    CHECK((pcm.iac.kicker_flags&1u) && pcm.iac.rpm_error_filtered!=0);
    CHECK(f.counts[PCM_ADC_FEEDBACK]==0 && f.adc_starts==380); /* 320 feedback, 10 each in 8, 0 and D, 30 in 2. */
    /* The phase6 observation precedes the first slot7 gain publication and
     * arms the low latch. Later slot7 caps let the consumer retain13. */
    CHECK(f.counts[PCM_AC_SWITCH_INPUTS]==0 && pcm.knock.activity==7);
    CHECK(pcm.knock.learning_low && !pcm.knock.learning_high && pcm.knock.retard==13 && pcm.knock.retard_limit==23);
    CHECK(pcm.runtime.refresh_requested && pcm.runtime.refresh_late);
    uint16_t compare; CHECK(read16(&f,PCM_TOC3,&compare)==PCM_OK);
    CHECK(compare==(uint16_t)(819u*160u));
}
static void test_busy_coalescing_and_call_order(void) {
    static Fixture f; Pcm pcm; init(&f,&pcm); f.inject=true; pcm.scheduler.phase=0;
    pcm.iac.target=255;
    CHECK(pcm_periodic_irq(&pcm)==PCM_OK);
    CHECK(f.counts[PCM_IAC_STEP]==0 && f.step_observations==4);
    CHECK(f.counts[PCM_COMMON_IO]==0 && f.shadow_observations==2 && pcm.scheduler.phase==2);
    CHECK(pcm.scheduler.busy_phase==1 && !pcm.scheduler.pending && !pcm.scheduler.busy);
    CHECK(f.counts[PCM_ADC_FEEDBACK]==0 && f.counts[PCM_CURRENT_CONTROL]==0);
    for (unsigned k=0;k<4;++k) CHECK(f.step_positions[k]==k+1);
    CHECK(pcm.iac.position==4 && f.observed_shadows[0]==0x14 && f.observed_shadows[1]==0x10);
    CHECK(f.current_writes==4 && f.timer_writes==4);
}
static void test_step_reset_cadence_and_busy_hold(void) {
    static Fixture f; Pcm pcm;
    for (unsigned reset=0;reset<2;++reset) {
        init(&f,&pcm);pcm.scheduler.busy=true;pcm.iac.position=255;
        pcm.iac.target=0;pcm.iac.step_control=1;pcm.iac.state_flags=(uint8_t)reset;
        for (unsigned phase=0;phase<160;++phase) {
            pcm.scheduler.phase=(uint8_t)phase;
            CHECK(pcm_periodic_irq(&pcm)==PCM_OK && pcm.scheduler.phase==phase);
        }
        CHECK(pcm.iac.position==(reset?135:95) && f.step_observations==160);
        CHECK(f.counts[PCM_COMMON_IO]==0 && f.shadow_observations==0);
        CHECK(pcm.scheduler.pending && pcm.scheduler.busy_phase==159);
    }
}
static void test_special_mode_and_slot_state(void) {
    static Fixture f; Pcm pcm; init(&f,&pcm); pcm.scheduler.phase=0x9f; pcm.runtime.special_fast_group=true;
    pcm.spark.first_reference=true;pcm.spark.output_request=pcm.reference.consumed=true;
    for (unsigned k=0;k<160;++k) CHECK(pcm_periodic_irq(&pcm)==PCM_OK);
    CHECK(f.counts[PCM_ALTERNATE_RPM]==0 && f.period_reads==80 && f.watchdog_writes==160);
    CHECK(!pcm.spark.output_request && !pcm.reference.consumed);
    CHECK(f.counts[PCM_COMMON_IO]==0 && f.counts[PCM_FUEL_CONTROL]==0);
    CHECK(f.counts[PCM_SLOT_00]==0 && f.counts[PCM_SLOT_0F]==0 && f.slot_f_diagnostic_writes==10);
}
static void test_retained_fields_profile_and_boundaries(void) {
    static Fixture f; Pcm pcm; init(&f,&pcm);
    pcm.scheduler.phase=0x9f; pcm.scheduler.run_counter=0xffff;
    pcm.runtime.spark_running=true; pcm.scheduler.clear_after_run_count=true;
    CHECK(pcm_phase_advance(&pcm)==PCM_OK);
    CHECK(pcm.scheduler.run_counter==0xffff && pcm.scheduler.clear_after_run_count);
    pcm.scheduler.phase=0x9f; pcm.scheduler.run_counter=9;
    CHECK(pcm_phase_advance(&pcm)==PCM_OK); CHECK(!pcm.scheduler.clear_after_run_count);
    pcm.scheduler.phase=7; pcm.scheduler.profiling_enabled=true;
    CHECK(write16(&f,PCM_TCNT,1000)==PCM_OK && write16(&f,PCM_TOC3,900)==PCM_OK);
    CHECK(pcm_profile_tail(&pcm)==PCM_OK && pcm.scheduler.peak_counts[7]==919);
    pcm.scheduler.pending=true;
    CHECK(pcm_profile_tail(&pcm)==PCM_OK && pcm.scheduler.peak_counts[7]==1738);
    init(&f,&pcm); pcm.runtime.engine_service=true; pcm.runtime.service_output_enable=true;
    pcm.runtime.service_output_value=true; pcm.runtime.inhibit_heartbeat=true;
    CHECK(pcm_main_pass(&pcm)==PCM_OK);
    CHECK(pcm.runtime.service_output_mirror && pcm.runtime.monitor_freeze);
    CHECK(pcm.runtime.output_override && pcm.runtime.first_conversion);
    for (unsigned action=1;action<=2;++action) {
        init(&f,&pcm);pcm.scheduler.phase=6;f.connection_action=action;
        pcm.scheduler.profiling_enabled=action==2;pcm.scheduler.peak_counts[7]=123;
        f.memory[PCM_EXTENSION_SIGNATURE]=0x7e;f.memory[PCM_EXTENSION_SIGNATURE+1]=0x18;
        f.memory[PCM_TCNT]=3;f.memory[PCM_TCNT+1]=0xe8;
        f.platform.task[PCM_SLOT_07]=NULL;
        f.platform.task[PCM_IAC_BACKGROUND]=NULL;pcm.iac.bank[0].no_ac_snapshot=99;
        CHECK(pcm_periodic_irq(&pcm)==PCM_OK && f.counts[PCM_CONNECTION_EXTENSION]==1);
        CHECK(f.counts[PCM_IAC_BACKGROUND]==0 && f.counts[PCM_SHIFT_LAMP]==0 && f.signature_reads==1);
        CHECK(pcm.iac.selected_snapshot==99);
        CHECK(pcm.scheduler.profiling_enabled==(action==1));
        CHECK(pcm.scheduler.peak_counts[7]==(action==1?1000:123));
    }
    init(&f,&pcm); pcm.runtime.factory_mode=true;
    CHECK(pcm_periodic_irq(&pcm)==PCM_FACTORY_BOUNDARY && f.used==0 && f.timer_writes==1);
    CHECK(pcm.scheduler.phase==0x0f && pcm.scheduler.timer_seen);
    init(&f,&pcm); f.guard_fails=true;
    CHECK(pcm_periodic_irq(&pcm)==PCM_STACK_BOUNDARY && f.used==0);
}
static void test_timer_stack_capture_and_recovery(void)
{
    static Fixture f;Pcm pcm;
    init(&f,&pcm);
    f.platform.capture_timer_stack_x=capture_stack_x;
    f.platform.check_stack=NULL;f.supplied_stack_x=0x03af;
    f.memory[0x004f]=0x84;f.memory[0x003a]=0x20;pcm.scheduler.busy=true;
    CHECK(pcm_periodic_irq(&pcm)==PCM_STACK_RECOVERY_BOUNDARY);
    CHECK(f.stack_captures==1 && f.timer_writes==1 && f.step_observations==0);
    CHECK(f.memory[0x003a]==0x28 && f.memory[0x004f]==0x80);
    CHECK(pcm.scheduler.timer_seen);
    CHECK(pcm.system.stack_recovery && !pcm.scheduler.busy && pcm.scheduler.pending);
    /* The provider committed canonical owners. The target LDS/SP recovery
     * outside the C frame is still a supplied precondition at this join. */
    CHECK(pcm_periodic_irq_resume(&pcm)==PCM_OK);
    CHECK(f.timer_writes==1 && f.step_observations==1);
    init(&f,&pcm);
    f.platform.capture_timer_stack_x=capture_stack_x;
    f.platform.check_stack=NULL;f.supplied_stack_x=0x03ee;
    f.memory[0x004f]=4;pcm.scheduler.busy=true;
    CHECK(pcm_periodic_irq(&pcm)==PCM_OK && f.stack_captures==1);
    CHECK(pcm.scheduler.busy && pcm.scheduler.pending && pcm.scheduler.busy_phase==0x0e);
    CHECK(f.timer_writes==1 && f.step_observations==1 && !pcm.system.stack_recovery);
    init(&f,&pcm);
    f.platform.capture_timer_stack_x=capture_stack_x;
    f.platform.check_stack=NULL;f.supplied_stack_x=0x03f7;
    f.memory[0x004f]=0;
    CHECK(pcm_periodic_irq(&pcm)==PCM_OK && f.stack_captures==1);
    CHECK(f.timer_writes==1 && f.step_observations==1);
    init(&f,&pcm);
    f.platform.capture_timer_stack_x=capture_stack_x;
    f.platform.check_stack=NULL;f.supplied_stack_x=0x03ef;
    f.memory[0x004f]=4;pcm.scheduler.busy=true;
    CHECK(pcm_periodic_irq(&pcm)==PCM_STACK_RECOVERY_BOUNDARY);
    CHECK(f.memory[0x003a]==8 && f.memory[0x004f]==0);
    CHECK(f.step_observations==0 && f.stack_captures==1);
    init(&f,&pcm);
    f.platform.capture_timer_stack_x=capture_stack_x;
    f.stack_capture_fail=true;f.platform.check_stack=NULL;
    CHECK(pcm_periodic_irq(&pcm)==PCM_NO_HARDWARE);
    CHECK(f.timer_writes==1 && f.step_observations==0 && f.stack_captures==1);
}
static void test_egr_state_handoff(void)
{
    static Fixture f;Pcm pcm;init(&f,&pcm);uint16_t word;uint8_t byte;
    f.memory[0x400d]=2;f.memory[0x70]=1;f.memory[0x1cc]=96;
    f.memory[0x4856]=f.memory[0x4857]=255;f.memory[0x47ce]=f.memory[0x47cf]=255;
    CHECK(pcm_egr_flow(&pcm)==PCM_OK && f.egr_fraction_writes==1);
    CHECK(pcm.spark.egr_fraction_high==0xfd && pcm.fuel.egr_fraction_low==2 && !pcm.spark.egr_active);
    pcm.fuel.corrected_pulse=1800;pcm.iac.blm_value=128;
    CHECK(pcm_fuel_egr_blm(&pcm)==PCM_OK && pcm.fuel.egr_subtract==444 && pcm.fuel.corrected_pulse==1356);
    pcm.spark.egr_fraction_high=0x12;pcm.fuel.egr_fraction_low=0x34;
    CHECK(read16(&f,0x1b2,&word)==PCM_OK && word==0x1234);
    CHECK(read8(&f,0x1b2,&byte)==PCM_OK && byte==0x12);
    CHECK(read8(&f,0x1b3,&byte)==PCM_OK && byte==0x34);
    CHECK(write8(&f,0x1b3,0xef)==PCM_OK && read16(&f,0x1b2,&word)==PCM_OK && word==0x12ef);
    CHECK(write8(&f,0x1b2,0xab)==PCM_OK && read16(&f,0x1b2,&word)==PCM_OK && word==0xabef);
    f.memory[0x6e]=9;pcm.spark.egr_active=true;
    CHECK(read8(&f,0x6e,&byte)==PCM_OK && byte==0x89);
    CHECK(write8(&f,0x6e,0x47)==PCM_OK && !pcm.spark.egr_active && f.memory[0x6e]==0x47);
}
/* Exercise the real ADC producer, $7C13 and the $3068 publication together. */
static int current_replay(void)
{
    static Fixture f;
    static const uint16_t inputs[] = {0x014d,0x014f,0x0150,0x0151,0x0153,0x0154,
        0x00b5,0x00fc,0x6e54,0x6e55,0x6e56,0x6e57,0x6e58};
    unsigned shadow, sample, battery, inhibit, fault;
    while (scanf("%u %u %u %u %u", &shadow,&sample,&battery,&inhibit,&fault)==5) {
        Pcm pcm;
        init(&f,&pcm);
        pcm.transmission.output_shadow=(uint8_t)shadow;
        pcm.spark.battery_sample=(uint8_t)battery;
        pcm.transmission.driver_inhibit=(inhibit & 1u)!=0;
        pcm.transmission.output_fault_flags=(uint8_t)fault;
        for (unsigned i=0; i<4; ++i) f.memory[PCM_ADR1+i]=(uint8_t)sample;
        for (unsigned i=0; i<sizeof(inputs)/sizeof(inputs[0]); ++i) {
            unsigned value;
            if (scanf("%u",&value)!=1) return 2;
            f.memory[inputs[i]]=(uint8_t)value;
        }
        for (unsigned pass=0; pass<3; ++pass) {
            CHECK(pcm_fast_service(&pcm)==PCM_OK);
            printf("%u %u %u %u %u %u %u %u %u\n", pcm.runtime.current_output,
                f.memory[0x14f], f.memory[0x150], f.memory[0x151], f.memory[0xfc],
                pcm.transmission.driver_inhibit, pcm.transmission.output_fault_flags,
                f.memory[PCM_CURRENT_COMMAND], f.memory[PCM_CURRENT_COMMAND+1]);
        }
    }
    return ferror(stdin)!=0;
}
static int spark_coolant_replay(void)
{
    static Fixture f;
    unsigned override, status, retard, coolant;
    while (scanf("%u %u %u %u",&override,&status,&retard,&coolant)==4) {
        Pcm pcm;
        init(&f,&pcm);
        f.memory[0x119]=(uint8_t)override;
        pcm.spark.transmission_status=(uint8_t)status;
        pcm.spark.transmission_retard=(uint8_t)retard;
        f.memory[0xa9]=(uint8_t)coolant;
        for (unsigned address=0x70b2; address<=0x70b7; ++address) {
            unsigned value;
            if (scanf("%u",&value)!=1) return 2;
            f.memory[address]=(uint8_t)value;
        }
        CHECK(pcm_transmission_spark_coolant(&pcm)==PCM_OK);
        printf("%u\n",pcm.spark.transmission_retard);
    }
    return ferror(stdin)!=0;
}
int main(int argc, char **argv) {
    if (argc==2 && strcmp(argv[1],"--spark-coolant")==0) return spark_coolant_replay();
    if (argc==2 && strcmp(argv[1],"--current")==0) return current_replay();
    if (argc==2 && strcmp(argv[1],"--fuel")==0) {
        unsigned d,t,v,e,p,a,f;
        while (scanf("%u %u %u %u %u %u %u",&d,&t,&v,&e,&p,&a,&f)==7) {
            if (d>65535 || t>65535 || v>255 || e>255 || p>65535 || a>255 || f>65535) return 2;
            PcmFuelBaseInputs in={(uint16_t)d,(uint16_t)t,(uint16_t)p,(uint16_t)f,(uint8_t)v,(uint8_t)e,(uint8_t)a};
            PcmFuelBase out=pcm_fuel_base(&in);
            printf("%u %u %u %u %u\n",out.displaced,out.air,out.air_rate,out.mixture_quotient,out.pulse);
        }
        return 0;
    }
    test_initialization_and_missing_contracts(); test_full_phase_cycle();
    test_busy_coalescing_and_call_order(); test_special_mode_and_slot_state();
    test_retained_fields_profile_and_boundaries();
    test_step_reset_cadence_and_busy_hold();
    test_timer_stack_capture_and_recovery();
    test_egr_state_handoff();
    puts("Eight kernel contract groups pass, including resident EGR cadence/fraction owners and timer recovery.");
    return 0;
}
