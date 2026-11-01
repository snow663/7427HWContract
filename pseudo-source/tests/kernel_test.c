#include "scheduler.h"
#include "hardware.h"
#include "control.h"
#include "calibration.h"
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
    bool masked, inject, injected, guard_fails, feed_reference;
    PcmPlatform platform;
} Fixture;
static PcmStatus read8(void *v, uint16_t a, uint8_t *out) { *out=((Fixture *)v)->memory[a]; return PCM_OK; }
static PcmStatus read16(void *v, uint16_t a, uint16_t *out) {
    Fixture *f=v;
    if (a==PCM_REFERENCE_PERIOD) ++f->period_reads;
    if (a==PCM_EXTENSION_SIGNATURE) ++f->signature_reads;
    *out=(uint16_t)((uint16_t)f->memory[a]*256u+f->memory[(uint16_t)(a+1u)]); return PCM_OK;
}
static PcmStatus write8(void *v, uint16_t a, uint8_t value) {
    Fixture *f=v; f->memory[a]=value;
    if (a==PCM_ADCTL) ++f->adc_starts;
    if (a==PCM_COPRST) {
        CHECK(value==((f->watchdog_writes&1u)?0x55:0xaa)); ++f->watchdog_writes;
    }
    return PCM_OK;
}
static PcmStatus write16(void *v, uint16_t a, uint16_t value) {
    Fixture *f=v; f->memory[a]=(uint8_t)(value>>8); f->memory[(uint16_t)(a+1u)]=(uint8_t)value;
    if (a==PCM_TOC3) ++f->timer_writes;
    if (a==PCM_CURRENT_COMMAND) ++f->current_writes;
    if (a==PCM_SPARK_TIMING_A) ++f->spark_writes;
    if (a==PCM_TCC_COMMAND) ++f->transmission_writes;
    return PCM_OK;
}
static PcmStatus mask_irq(void *v, bool value) { ((Fixture *)v)->masked=value; return PCM_OK; }
static PcmStatus guard(void *v, bool busy) {
    Fixture *f=v; (void)busy; return f->guard_fails?PCM_STACK_BOUNDARY:PCM_OK;
}
static PcmStatus task(Pcm *pcm, PcmTask id) {
    Fixture *f=pcm->platform->context;
    CHECK(f->used<sizeof(f->trace)/sizeof(f->trace[0]));
    f->trace[f->used++]=id; ++f->counts[id];
    if (id==PCM_SLOT_02) CHECK(f->masked);
    if (id==PCM_CURRENT_CONTROL) pcm->runtime.current_output=0x42;
    if (id==PCM_CONNECTION_EXTENSION && f->connection_action)
        pcm->scheduler.profiling_enabled=f->connection_action==1;
    if (id==PCM_INPUT_HOUSEKEEPING && f->feed_reference) {
        pcm->reference.pending=true;pcm->spark.map_filtered=135;pcm->knock.retard=13;
    }
    if (id==PCM_COMMON_IO && f->inject && !f->injected) {
        f->injected=true;
        for (unsigned k=0;k<3;++k) CHECK(pcm_periodic_irq(pcm)==PCM_OK);
    }
    return PCM_OK;
}
static void init(Fixture *f, Pcm *pcm) {
    memset(f,0,sizeof(*f)); memset(pcm,0,sizeof(*pcm));
    f->platform.context=f; f->platform.read8=read8; f->platform.read16=read16;
    f->platform.write8=write8; f->platform.write16=write16; f->platform.mask_irq=mask_irq;
    f->platform.check_stack=guard;
    for (unsigned k=0;k<PCM_TASK_COUNT;++k) f->platform.task[k]=task;
    pcm->platform=&f->platform; pcm->calibration=&pcm_reference_scheduler_calibration;
    pcm->scheduler.phase=0x0e;
}
static void test_initialization_and_missing_contracts(void) {
    static Fixture f; Pcm pcm; init(&f,&pcm);
    f.memory[PCM_TCNT]=0xff; f.memory[PCM_TCNT+1]=0xfc;
    pcm.knock.sample_baseline=0xabcd; pcm.knock.observation_accumulator=0x55;
    pcm.knock.retard=0x23; pcm.knock.sensor_fault=true; pcm.knock.sensor_fault_count=0x64;
    pcm.spark.command=0xabcd; pcm.runtime.adc_timeout=true; pcm.runtime.adc_fault=true;
    pcm.transmission.output_shadow=0xff;pcm.transmission.tcc_command=0xabcd;
    CHECK(pcm_reset_sequence(&pcm,&f.platform,&pcm_reference_scheduler_calibration)==PCM_OK);
    CHECK(pcm.scheduler.phase==0x0e && f.masked);
    CHECK(pcm.knock.sample_baseline==0 && pcm.knock.observation_accumulator==0);
    CHECK(pcm.knock.retard==0 && !pcm.knock.sensor_fault && pcm.knock.sensor_fault_count==0);
    CHECK(pcm.spark.command==0 && !pcm.runtime.adc_timeout && !pcm.runtime.adc_fault);
    CHECK(pcm.transmission.output_shadow==0 && pcm.transmission.tcc_command==0);
    CHECK(f.memory[PCM_TOC3]==0 && f.memory[PCM_TOC3+1]==4);
    CHECK(f.memory[PCM_TMSK1]==0xa0);
    static const PcmTask expected[]={PCM_RESET_ENTRY,PCM_RESET_RAM,
        PCM_RESET_SENSORS,PCM_RESET_RETAINED,PCM_RESET_CONTROLLERS,PCM_RESET_SERIAL};
    CHECK(f.used==sizeof(expected)/sizeof(expected[0]));
    CHECK(memcmp(f.trace,expected,sizeof(expected))==0);
    init(&f,&pcm); f.platform.task[PCM_COMMON_IO]=NULL;
    CHECK(pcm_main_pass(&pcm)==PCM_UNIMPLEMENTED);
    CHECK(pcm.unresolved_task==PCM_COMMON_IO && f.counts[PCM_FUEL_CONTROL]==0);
    pcm.platform=NULL; CHECK(pcm_watchdog_service(&pcm)==PCM_NO_HARDWARE);
}
static void test_full_phase_cycle(void) {
    static Fixture f; Pcm pcm; init(&f,&pcm); pcm.scheduler.phase=0x9f;
    f.feed_reference=true;pcm.runtime.spark_running=pcm.runtime.fuel_running=true;
    pcm.reference.coolant=200;pcm.spark.load_coordinate=128;pcm.spark.previous_load=128;
    pcm.knock.retard=13;pcm.knock.activity=7;pcm.knock.learning_high=true;
    for (unsigned k=0;k<160;++k) {
        CHECK(pcm_periodic_irq(&pcm)==PCM_OK);
        CHECK(pcm.scheduler.phase==k && !pcm.scheduler.busy);
    }
    CHECK(f.counts[PCM_IAC_STEP]==160 && f.current_writes==160);
    CHECK(f.counts[PCM_COMMON_IO]==160 && f.counts[PCM_INPUT_HOUSEKEEPING]==80);
    CHECK(f.counts[PCM_SPARK_CONTROL]==0 && f.spark_writes==80 && f.counts[PCM_FUEL_CONTROL]==80);
    CHECK(f.counts[PCM_TRANSMISSION_INPUT]==40 && f.counts[PCM_PRESSURE_TCC]==40);
    CHECK(f.counts[PCM_SHIFT_CONTROL]==40 && f.counts[PCM_IAC_CONTROL]==40);
    for (unsigned k=PCM_SLOT_00;k<=PCM_SLOT_0F;++k)
        CHECK(f.counts[k]==(k==PCM_SLOT_07 || k==PCM_SLOT_0E?0u:10u));
    CHECK(f.signature_reads==10 && f.transmission_writes==10 && f.counts[PCM_CONNECTION_EXTENSION]==0);
    CHECK(f.counts[PCM_IAC_BACKGROUND]==10 && f.counts[PCM_SHIFT_LAMP]==10);
    CHECK(f.adc_starts==10); /* Slot8 now runs its real diagnostic, without a task binding. */
    /* The phase6 observation precedes the first slot7 gain publication and
     * arms the low latch. Later slot7 caps let the consumer retain13. */
    CHECK(f.counts[PCM_AC_SWITCH_INPUTS]==10 && pcm.knock.activity==7);
    CHECK(pcm.knock.learning_low && !pcm.knock.learning_high && pcm.knock.retard==13 && pcm.knock.retard_limit==23);
    CHECK(pcm.runtime.refresh_requested && pcm.runtime.refresh_late);
    uint16_t compare; CHECK(read16(&f,PCM_TOC3,&compare)==PCM_OK);
    CHECK(compare==(uint16_t)(819u*160u));
}
static void test_busy_coalescing_and_call_order(void) {
    static Fixture f; Pcm pcm; init(&f,&pcm); f.inject=true; pcm.scheduler.phase=0;
    CHECK(pcm_periodic_irq(&pcm)==PCM_OK);
    CHECK(f.counts[PCM_IAC_STEP]==4 && f.counts[PCM_CURRENT_CONTROL]==4);
    CHECK(f.counts[PCM_COMMON_IO]==2 && pcm.scheduler.phase==2);
    CHECK(pcm.scheduler.busy_phase==1 && !pcm.scheduler.pending && !pcm.scheduler.busy);
    CHECK(f.trace[0]==PCM_IAC_STEP && f.trace[1]==PCM_ADC_FEEDBACK && f.trace[2]==PCM_CURRENT_CONTROL);
    CHECK(f.current_writes==4 && f.timer_writes==4);
}
static void test_special_mode_and_slot_state(void) {
    static Fixture f; Pcm pcm; init(&f,&pcm); pcm.scheduler.phase=0x9f; pcm.runtime.special_fast_group=true;
    pcm.spark.first_reference=true;pcm.spark.output_request=pcm.reference.consumed=true;
    for (unsigned k=0;k<160;++k) CHECK(pcm_periodic_irq(&pcm)==PCM_OK);
    CHECK(f.counts[PCM_ALTERNATE_RPM]==0 && f.period_reads==80 && f.watchdog_writes==160);
    CHECK(!pcm.spark.output_request && !pcm.reference.consumed);
    CHECK(f.counts[PCM_COMMON_IO]==0 && f.counts[PCM_FUEL_CONTROL]==0);
    CHECK(f.counts[PCM_SLOT_00]==10 && f.counts[PCM_SLOT_0F]==10);
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
        CHECK(pcm_periodic_irq(&pcm)==PCM_OK && f.counts[PCM_CONNECTION_EXTENSION]==1);
        CHECK(f.counts[PCM_IAC_BACKGROUND]==1 && f.counts[PCM_SHIFT_LAMP]==1 && f.signature_reads==1);
        CHECK(pcm.scheduler.profiling_enabled==(action==1));
        CHECK(pcm.scheduler.peak_counts[7]==(action==1?1000:123));
    }
    init(&f,&pcm); pcm.runtime.factory_mode=true;
    CHECK(pcm_periodic_irq(&pcm)==PCM_FACTORY_BOUNDARY && f.used==0 && f.timer_writes==1);
    init(&f,&pcm); f.guard_fails=true;
    CHECK(pcm_periodic_irq(&pcm)==PCM_STACK_BOUNDARY && f.used==0);
}
int main(int argc, char **argv) {
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
    puts("Five kernel contract groups passed, including resident spark/alternate calls; other controller dependencies remain explicit.");
    return 0;
}
