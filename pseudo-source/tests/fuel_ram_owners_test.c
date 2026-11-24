#include "fuel.h"
#include "fuel_ram_owners.h"
#include "hardware.h"
#include "serial.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define CHECK(x) do { if(!(x)){fprintf(stderr,"Fuel RAM owner %s:%d: %s\n",__FILE__,__LINE__,#x);exit(1);} }while(0)

typedef struct {
    PcmPlatform platform;
    Pcm *pcm;
    uint8_t provider[65536]; /* host test ONLY, no target shadow */
    unsigned attempts, fail_at;
    bool masked;
} Fixture;
static PcmStatus operation(Fixture *f)
{
    ++f->attempts;
    return f->fail_at==f->attempts?PCM_NO_HARDWARE:PCM_OK;
}
static PcmStatus read8(void *ctx,uint16_t address,uint8_t *out)
{
    Fixture *f=ctx;
    PcmStatus result=operation(f);if(result!=PCM_OK)return result;
    *out=f->provider[address];
    return PCM_OK;
}
static PcmStatus read16(void *ctx,uint16_t address,uint16_t *out)
{
    Fixture *f=ctx;
    PcmStatus result=operation(f);if(result!=PCM_OK)return result;
    *out=(uint16_t)(((uint16_t)f->provider[address]<<8)|
                 f->provider[(uint16_t)(address+1u)]);
    return PCM_OK;
}
static PcmStatus write8(void *ctx,uint16_t address,uint8_t value)
{
    Fixture *f=ctx;
    PcmStatus result=operation(f);if(result!=PCM_OK)return result;
    f->provider[address]=value;
    return PCM_OK;
}
static PcmStatus write16(void *ctx,uint16_t address,uint16_t value)
{
    Fixture *f=ctx;
    PcmStatus result=operation(f);if(result!=PCM_OK)return result;
    f->provider[address]=(uint8_t)(value>>8);
    f->provider[(uint16_t)(address+1u)]=(uint8_t)value;
    return PCM_OK;
}
static PcmStatus mask(void *ctx,bool on)
{
    Fixture *f=ctx;
    PcmStatus result=operation(f);if(result!=PCM_OK)return result;
    f->masked=on;return PCM_OK;
}
static void init(Fixture *f,Pcm *pcm)
{
    memset(f,0,sizeof(*f));memset(pcm,0,sizeof(*pcm));
    f->pcm=pcm;f->platform.context=f;f->platform.read8=read8;
    f->platform.read16=read16;f->platform.write8=write8;
    f->platform.write16=write16;f->platform.mask_irq=mask;
    f->platform.bind_fuel_ram_owners=true;
    pcm->platform=&f->platform;
    f->provider[0x0004]=0x60; /* unowned bits 6/5 survive owned writes */
    f->provider[0x0044]=0x20; /* unowned bit5 survives */
    f->provider[0x004f]=0x02; /* unowned bit1 survives */
    f->provider[0x0051]=0x12; /* unowned bits4/1 survive */
    f->provider[0x0086]=0x16; /* unowned bits4/2/1 survive */
    f->provider[0x4009]=0;f->provider[0x400a]=16;
    pcm->system.fuel_ignition_counter=8;
    pcm->reference.latch_inhibited=true;
    pcm->runtime.spark_running=pcm->runtime.fuel_running=true;
    pcm->spark.bypass_supervision=true;
    pcm->fuel.oxygen_activity=pcm->fuel.oxygen_warmed=true;
    pcm->spark.run_transition=true;
    pcm->scheduler.clear_after_run_count=true; /* unmasked $0004.4 survives */
    pcm->reference.bank_fault=pcm->spark.est_fault=true;
    pcm->scheduler.run_counter=0x1234;
    pcm->reference.delivered_pulse=0x5678;
    pcm->reference.rpm_coordinate=75;
    pcm->reference.crank_references=13;
    pcm->reference.event_age=17;
    pcm->reference.enrichment_age=28;
    pcm->runtime.ignition_off=false;
    pcm->system.retained_initialized=true;
    pcm->scheduler.profiling_enabled=true;
    pcm->spark.first_reference=true;
    pcm->fuel.closed_seen=true;
    pcm->io.egr_failure_count=53;
    pcm->fuel.startup_park_hold=25;
    pcm->io.coolant_context=0xfbu;
}
static void test_reset_and_word_alias(void)
{
    static Fixture f;Pcm p;init(&f,&p);
    CHECK(pcm_fuel_ignition_precheck(&p)==PCM_OK);
    CHECK(p.system.fuel_ignition_counter==9);
    CHECK(p.scheduler.run_counter==0 && p.reference.delivered_pulse==0);
    CHECK(!p.runtime.spark_running && !p.runtime.fuel_running);
    CHECK(!p.spark.bypass_supervision && !p.fuel.oxygen_activity && !p.fuel.oxygen_warmed);
    CHECK(!p.spark.run_transition && !p.reference.bank_fault && !p.spark.est_fault);
    CHECK(p.reference.rpm_coordinate==0 && p.reference.crank_references==0);
    CHECK(p.reference.event_age==0 && p.reference.enrichment_age==0);
    CHECK(p.runtime.ignition_off && !p.system.retained_initialized);
    CHECK(p.scheduler.profiling_enabled && p.spark.first_reference);
    CHECK(f.provider[PCM_COPRST]==0x55 && !f.masked);
    uint8_t byte;
    CHECK(pcm_read8(&p,0x0004,&byte)==PCM_OK && byte==0x70); /* residual60 + bit4 */
    CHECK(pcm_read8(&p,0x0044,&byte)==PCM_OK && (byte&0x20u));
    CHECK(pcm_read8(&p,0x004f,&byte)==PCM_OK && byte==0x02);
    CHECK(pcm_read8(&p,0x0086,&byte)==PCM_OK && (byte&0x40u) && !(byte&8u));
    CHECK(pcm_read8(&p,0x027e,&byte)==PCM_OK && byte==0);
    CHECK(pcm_read8(&p,0x027f,&byte)==PCM_OK && byte==9);
    CHECK(pcm_write8(&p,0x027e,0x12)==PCM_OK);
    CHECK(pcm_write8(&p,0x027f,0x34)==PCM_OK);
    CHECK(p.system.fuel_ignition_counter==0x1234);
    CHECK(pcm_read8(&p,0x027e,&byte)==PCM_OK && byte==0x12);
    CHECK(pcm_read8(&p,0x027f,&byte)==PCM_OK && byte==0x34);
    CHECK(!pcm_fuel_ram_owner_read8(&p,0x0bad,0,NULL));
    CHECK(!pcm_fuel_ram_owner_write8(&p,0x0bad,123));
    CHECK(!pcm_fuel_ram_owner_read16(&p,0x0bad,NULL));
    CHECK(!pcm_fuel_ram_owner_write16(&p,0x0bad,123));
}
static void test_ignition_off_single_clear(void)
{
    static Fixture f;Pcm p;init(&f,&p);
    p.reference.latch_inhibited=false;
    p.runtime.ignition_off=true;
    p.system.fuel_ignition_counter=501;
    CHECK(pcm_fuel_ignition_precheck(&p)==PCM_OK);
    CHECK(p.system.fuel_ignition_counter==0);
    CHECK(!p.runtime.ignition_off && !p.fuel.closed_seen);
    CHECK(!p.spark.first_reference && !(p.io.coolant_context&8u));
    CHECK(p.io.egr_failure_count==0 && p.fuel.startup_park_hold==0);
    CHECK(p.system.retained_initialized);
    CHECK(p.runtime.spark_running && p.runtime.fuel_running);
    CHECK(p.scheduler.run_counter==0x1234 && p.reference.delivered_pulse==0x5678);
    p.io.egr_failure_count=77;p.fuel.startup_park_hold=60;
    CHECK(pcm_fuel_ignition_precheck(&p)==PCM_OK);
    CHECK(p.io.egr_failure_count==77 && p.fuel.startup_park_hold==60);
}
static void test_gate_halt_and_failure_prefix(void)
{
    static Fixture f;Pcm p;
    init(&f,&p);p.system.fuel_ignition_counter=7;
    CHECK(pcm_fuel_ignition_precheck(&p)==PCM_OK);
    CHECK(p.system.fuel_ignition_counter==8);
    CHECK(p.runtime.fuel_running && p.runtime.spark_running);
    init(&f,&p);p.system.fuel_ignition_counter=16;
    CHECK(pcm_fuel_ignition_precheck(&p)==PCM_HALT_BOUNDARY);
    CHECK(f.masked && f.provider[0x3039]==8);
    CHECK(p.system.fuel_ignition_counter==16 && f.provider[PCM_COPRST]==0);
    CHECK(!p.runtime.spark_running && !p.runtime.fuel_running);
    init(&f,&p);f.fail_at=4;
    CHECK(pcm_fuel_ignition_precheck(&p)==PCM_NO_HARDWARE);
    CHECK(p.runtime.fuel_running && p.spark.bypass_supervision);
    CHECK(f.attempts==4);
    init(&f,&p);f.fail_at=5;
    CHECK(pcm_fuel_ignition_precheck(&p)==PCM_NO_HARDWARE);
    CHECK(!p.spark.bypass_supervision && !p.fuel.oxygen_activity);
    CHECK(p.reference.bank_fault && p.spark.est_fault);
    CHECK(p.runtime.spark_running && p.runtime.fuel_running);
    CHECK(f.attempts==5);
}
static void test_roundtrip_shared_bits(void)
{
    static Fixture f;Pcm p;init(&f,&p);
    const uint16_t words[]={0x00fd,0x024c,0x027e,0x01d2};
    for(unsigned n=0;n<4;++n) {
        uint16_t a=words[n],v;
        CHECK(pcm_write16(&p,a,0x55aau)==PCM_OK);
        CHECK(pcm_read16(&p,a,&v)==PCM_OK && v==0x55aau);
        CHECK(pcm_write8(&p,a,0x12)==PCM_OK);
        CHECK(pcm_write8(&p,(uint16_t)(a+1),0x34)==PCM_OK);
        CHECK(pcm_read16(&p,a,&v)==PCM_OK && v==0x1234u);
    }
    const uint16_t bytes[]={0x0004,0x0019,0x003e,0x0041,0x0044,
      0x0046,0x0047,0x004f,0x0050,0x0051,0x0086};
    for(unsigned n=0;n<sizeof(bytes)/sizeof(bytes[0]);++n) {
        uint16_t a=bytes[n];uint8_t old,after;
        CHECK(pcm_read8(&p,a,&old)==PCM_OK);
        CHECK(pcm_write8(&p,a,(uint8_t)(old^0xffu))==PCM_OK);
        CHECK(pcm_read8(&p,a,&after)==PCM_OK);
        CHECK(after==(uint8_t)(old^0xffu));
    }
}
static void test_binding_is_opt_in(void)
{
    static Fixture f;Pcm p;uint8_t value;
    init(&f,&p);
    f.platform.bind_fuel_ram_owners=false;
    CHECK(pcm_read8(&p,0x004f,&value)==PCM_OK && value==0x02);
    CHECK(pcm_write8(&p,0x004f,0)==PCM_OK);
    CHECK(p.runtime.fuel_running && p.runtime.spark_running);
    init(&f,&p);
    CHECK(pcm_read8(&p,0x004f,&value)==PCM_OK && value==0x92);
    CHECK(pcm_write8(&p,0x004f,0)==PCM_OK);
    CHECK(!p.runtime.fuel_running && !p.runtime.spark_running);
}
static void test_board_and_vss_named_ram(void)
{
    static Fixture f;Pcm p;init(&f,&p);
    p.io.output_context=0x21;
    p.spark.output_request=true;
    p.iac.kicker_request=true;
    p.transmission.output_shadow=0xa5;
    p.iac.input_shadow=0x43;
    p.io.auxiliary_output=0x56;
    uint8_t b;
    CHECK(pcm_read8(&p,0x004b,&b)==PCM_OK && b==0xb1);
    CHECK(pcm_read8(&p,0x004c,&b)==PCM_OK && b==0xa5);
    CHECK(pcm_read8(&p,0x004d,&b)==PCM_OK && b==0x43);
    CHECK(pcm_read8(&p,0x004e,&b)==PCM_OK && b==0x56);
    CHECK(pcm_write8(&p,0x004b,0x4fu)==PCM_OK);
    CHECK(p.io.output_context==0x4fu && !p.spark.output_request &&
          !p.iac.kicker_request);
    CHECK(pcm_write8(&p,0x004c,0x77)==PCM_OK &&
          p.transmission.output_shadow==0x77);
    CHECK(pcm_write8(&p,0x004d,0x88)==PCM_OK &&
          p.iac.input_shadow==0x88);
    CHECK(pcm_write8(&p,0x004e,0x99)==PCM_OK &&
          p.io.auxiliary_output==0x99);
    p.spark.vehicle_speed_high=0x66;
    p.io.vehicle_speed_fraction=0x77;
    p.io.vss_previous=0x1122;
    p.io.vss_raw=0x3344;
    p.io.vss_age=0x55;
    uint16_t word;
    CHECK(pcm_read16(&p,0x0284,&word)==PCM_OK && word==0x6677);
    CHECK(pcm_read16(&p,0x080f,&word)==PCM_OK && word==0x1122);
    CHECK(pcm_read16(&p,0x0812,&word)==PCM_OK && word==0x3344);
    CHECK(pcm_read8(&p,0x0811,&b)==PCM_OK && b==0x55);
    CHECK(pcm_write16(&p,0x0284,0xabcd)==PCM_OK &&
          p.spark.vehicle_speed_high==0xab &&
          p.io.vehicle_speed_fraction==0xcd);
    CHECK(pcm_write8(&p,0x0285,0xef)==PCM_OK &&
          p.spark.vehicle_speed_high==0xab &&
          p.io.vehicle_speed_fraction==0xef);
    CHECK(pcm_write16(&p,0x080f,0x1234)==PCM_OK &&
          p.io.vss_previous==0x1234);
    CHECK(pcm_write16(&p,0x0812,0x5678)==PCM_OK && p.io.vss_raw==0x5678);
    CHECK(pcm_write8(&p,0x0813,0x9a)==PCM_OK && p.io.vss_raw==0x569a);
    CHECK(pcm_write8(&p,0x0811,0x33)==PCM_OK && p.io.vss_age==0x33);
    f.fail_at=f.attempts+1;
    CHECK(pcm_write16(&p,0x0812,0xf00d)==PCM_NO_HARDWARE);
    CHECK(p.io.vss_raw==0x569a);
}
static void test_engine_owners_and_aldl(void)
{
    static Fixture f;Pcm p;init(&f,&p);
    p.scheduler.timer_seen=true;p.system.interrupt_flags=0x54;
    p.scheduler.phase=0xb5;p.scheduler.busy_phase=0x73;
    p.iac.position=0x12;p.iac.target=0x34;p.iac.step_control=0x56;
    p.runtime.adc_fault=true;p.system.rom_failure=true;
    p.system.stack_recovery=true;p.scheduler.pending=true;
    p.system.adaptive_failure=true;
    p.spark.idle_state=true;p.spark.idle_feedback=true;
    p.reference.pending=true;p.runtime.diagnostic_switch=true;
    p.reference.consumed=true;p.reference.sample_map=true;
    uint8_t v=0;
    f.provider[0x003a]=0x90; /* shared unknown bits 7/4 */
    CHECK(pcm_read8(&p,0x0000,&v)==PCM_OK && v==0x55);
    CHECK(pcm_read8(&p,0x0002,&v)==PCM_OK && v==0xb5);
    CHECK(pcm_read8(&p,0x0003,&v)==PCM_OK && v==0x73);
    CHECK(pcm_read8(&p,0x0007,&v)==PCM_OK && v==0x12);
    CHECK(pcm_read8(&p,0x0008,&v)==PCM_OK && v==0x34);
    CHECK(pcm_read8(&p,0x000a,&v)==PCM_OK && v==0x56);
    CHECK(pcm_read8(&p,0x003a,&v)==PCM_OK && v==0xfb);
    CHECK(pcm_read8(&p,0x0050,&v)==PCM_OK && v==0xf5);
    CHECK(pcm_write8(&p,0x003a,0x90)==PCM_OK);
    CHECK(!p.runtime.adc_fault && !p.scheduler.pending &&
          !p.system.rom_failure && !p.system.stack_recovery);
    CHECK((f.provider[0x003a]&0x90u)==0x90u);
    CHECK(pcm_write8(&p,0x0050,0x0b)==PCM_OK);
    CHECK(!p.reference.pending && p.io.diagnostic_warm &&
          p.fuel.idle_afr_ready && p.reference.sample_map);
    CHECK(pcm_write8(&p,0x0002,0xcc)==PCM_OK && p.scheduler.phase==0xcc);
    CHECK(pcm_write8(&p,0x0007,0xa4)==PCM_OK && p.iac.position==0xa4);
    CHECK(pcm_write8(&p,0x0008,0xa5)==PCM_OK && p.iac.target==0xa5);
    CHECK(pcm_write8(&p,0x000a,0xa6)==PCM_OK && p.iac.step_control==0xa6);

    p.spark.rpm_high=0x12;p.spark.rpm_fraction=0x34;
    p.reference.load_filtered=0x2345;p.reference.load_event=0x3456;
    p.spark.command=0x4567;p.spark.command_latched=0x5678;
    p.spark.composite=0x6789;p.fuel.corrected_pulse=0x789a;
    p.reference.timer_pulse=0x89ab;p.reference.running_packet=0x9abc;
    p.reference.crank_seed=0xabcd;p.fuel.pe_vehicle_change=0xbcde;
    p.fuel.authorization_capture=0xcdef;p.iac.airflow=0xdef0;
    const struct {uint16_t address, expected;} words[]={
      {0x0063,0x1234},{0x0068,0x2345},{0x006a,0x3456},
      {0x01ee,0x4567},{0x01f0,0x5678},{0x01fd,0x6789},
      {0x024e,0x789a},{0x0250,0x89ab},{0x0254,0x9abc},
      {0x02cf,0xabcd},{0x0818,0xbcde},{0x0851,0xcdef},{0x088b,0xdef0}
    };
    for(size_t i=0;i<sizeof(words)/sizeof(words[0]);++i){
        uint16_t x=0;
        uint16_t a=words[i].address;
        CHECK(pcm_read16(&p,a,&x)==PCM_OK && x==words[i].expected);
        CHECK(pcm_read8(&p,a,&v)==PCM_OK && v==(uint8_t)(x>>8));
        CHECK(pcm_read8(&p,(uint16_t)(a+1u),&v)==PCM_OK &&
              v==(uint8_t)x);
        CHECK(pcm_write16(&p,a,0xaced)==PCM_OK);
        CHECK(pcm_read16(&p,a,&x)==PCM_OK && x==0xaced);
        CHECK(pcm_write8(&p,(uint16_t)(a+1u),0x42)==PCM_OK);
        CHECK(pcm_read16(&p,a,&x)==PCM_OK && x==0xac42);
        CHECK(f.provider[a]==0xac && f.provider[a+1u]==0x42);
    }
    CHECK(p.spark.rpm_high==0xac && p.spark.rpm_fraction==0x42);
    CHECK(p.spark.command==0xac42 && p.spark.composite==0xac42);
    CHECK(p.fuel.corrected_pulse==0xac42 && p.iac.airflow==0xac42);
    f.fail_at=f.attempts+1;
    CHECK(pcm_write16(&p,0x01fd,0x8899)==PCM_NO_HARDWARE);
    CHECK(p.spark.composite==0xac42);
}
static void test_serial_owner_unification(void)
{
    static Fixture f;Pcm p;init(&f,&p);
    p.serial.sessions=0x31;
    p.serial.descriptor=0xa55a;
    p.serial.receive[0]=0x22;p.serial.receive[33]=0x77;
    p.serial.engine_command=0xf0;p.serial.transmission_command=0x69;
    p.runtime.monitor_freeze=true;
    p.serial.busy=true;
    uint8_t value;
    uint16_t word;
    CHECK(pcm_read8(&p,0x0042,&value)==PCM_OK && value==0x31);
    CHECK(pcm_serial_memory_read8(&p,0x0042,&value)==PCM_OK && value==0x31);
    CHECK(pcm_read8(&p,0x003b,&value)==PCM_OK && value==0x44);
    CHECK(pcm_read16(&p,0x0362,&word)==PCM_OK && word==0xa55a);
    CHECK(pcm_serial_memory_read16(&p,0x0362,&word)==PCM_OK && word==0xa55a);
    CHECK(pcm_read8(&p,0x036c,&value)==PCM_OK && value==0x22);
    CHECK(pcm_read8(&p,0x038d,&value)==PCM_OK && value==0x77);
    CHECK(pcm_read8(&p,0x038e,&value)==PCM_OK && value==0xf0);
    CHECK(pcm_read8(&p,0x0399,&value)==PCM_OK && value==0x69);

    CHECK(pcm_write8(&p,0x0042,0x80)==PCM_OK && p.serial.sessions==0x80);
    CHECK(pcm_serial_memory_write8(&p,0x0042,0x63)==PCM_OK);
    CHECK(pcm_read8(&p,0x0042,&value)==PCM_OK && value==0x63);
    CHECK(pcm_write8(&p,0x003b,0x95)==PCM_OK);
    CHECK(p.serial.clear_transmission && !p.serial.clear_engine &&
          p.runtime.monitor_freeze && !p.serial.busy &&
          p.serial.companion_pending);
    CHECK(pcm_write16(&p,0x0362,0x1234)==PCM_OK && p.serial.descriptor==0x1234);
    CHECK(pcm_serial_memory_write8(&p,0x0363,0x56)==PCM_OK &&
          p.serial.descriptor==0x1256);
    CHECK(pcm_read16(&p,0x0362,&word)==PCM_OK && word==0x1256);
    CHECK(pcm_write8(&p,0x036c,0x99)==PCM_OK && p.serial.receive[0]==0x99);
    CHECK(pcm_serial_memory_write8(&p,0x038d,0xaa)==PCM_OK &&
          p.serial.receive[33]==0xaa);
    CHECK(pcm_read16(&p,0x038d,&word)==PCM_OK && word==0xaaf0);
    CHECK(pcm_write16(&p,0x0368,0xabcd)==PCM_OK &&
          p.serial.service_age==0xabcd);
    CHECK(pcm_write16(&p,0x036a,0x55aa)==PCM_OK &&
          p.serial.service_expiry==0x55aa);
    CHECK(pcm_serial_memory_write8(&p,0x0399,0x41)==PCM_OK);
    CHECK(pcm_read8(&p,0x0399,&value)==PCM_OK && value==0x41);
    f.fail_at=f.attempts+1;
    CHECK(pcm_write16(&p,0x0362,0xffff)==PCM_NO_HARDWARE);
    CHECK(p.serial.descriptor==0x1256);
}
static void test_mixed_owner_word_transactions(void)
{
    static Fixture f;Pcm p;init(&f,&p);
    /* 0041 is shared bit state; 0042 is the serial session byte.
     * Both must be coherent from a single physical 16-bit sample. */
    f.provider[0x0041]=0x83;
    f.provider[0x0042]=0;
    p.iac.park_neutral=true;
    p.io.ac_mirror=false;
    p.fuel.ac_enrichment_seen=true;
    p.serial.sessions=0x5c;
    unsigned start=f.attempts;
    uint16_t word=0;
    CHECK(pcm_read16(&p,0x0041,&word)==PCM_OK && word==0xab5c);
    CHECK(f.attempts==start+1);
    CHECK(pcm_serial_memory_read16(&p,0x0041,&word)==PCM_OK &&
          word==0xab5c);
    CHECK(pcm_write16(&p,0x0041,0x9277)==PCM_OK);
    CHECK(!p.iac.park_neutral && p.io.ac_mirror &&
          !p.fuel.ac_enrichment_seen && p.serial.sessions==0x77);
    CHECK(f.provider[0x0041]==0x92 && f.provider[0x0042]==0x77);
    CHECK(pcm_read16(&p,0x0041,&word)==PCM_OK && word==0x9277);
    /* The 003A/003B word crosses scheduler/fault and serial owners. */
    f.provider[0x003a]=0x90;
    p.runtime.adc_fault=true;
    p.scheduler.pending=true;
    p.serial.busy=true;
    CHECK(pcm_read16(&p,0x003a,&word)==PCM_OK && word==0xb140);
    CHECK(pcm_write16(&p,0x003a,0x1155)==PCM_OK);
    CHECK(!p.scheduler.pending && p.runtime.adc_fault &&
          p.serial.busy && p.serial.clear_transmission);
    /* The 004B/004C word crosses board shadow field owners. */
    p.io.output_context=0x21;
    p.spark.output_request=true;
    p.iac.kicker_request=false;
    p.transmission.output_shadow=0xa2;
    CHECK(pcm_read16(&p,0x004b,&word)==PCM_OK && word==0x31a2);
    CHECK(pcm_write16(&p,0x004b,0x80ed)==PCM_OK);
    CHECK(p.iac.kicker_request && !p.spark.output_request &&
          p.transmission.output_shadow==0xed);
    unsigned before=f.attempts;
    f.fail_at=before+1;
    CHECK(pcm_write16(&p,0x0041,0xffff)==PCM_NO_HARDWARE);
    CHECK(f.attempts==before+1 && p.serial.sessions==0x77 &&
          p.io.ac_mirror);
}
int main(int argc,char **argv)
{
    if(argc==2 && strcmp(argv[1],"--contracts")!=0)return 2;
    test_binding_is_opt_in();test_reset_and_word_alias();test_ignition_off_single_clear();
    test_gate_halt_and_failure_prefix();test_roundtrip_shared_bits();
    test_board_and_vss_named_ram();
    test_engine_owners_and_aldl();
    test_serial_owner_unification();
    test_mixed_owner_word_transactions();
    puts("Fuel prelude canonical RAM provider aliases, split-word bytes and failure prefixes passed.");
    return 0;
}
