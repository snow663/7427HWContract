#include "hc11_bus.h"
#include "hc11_ram_sync.h"
#include "hardware.h"
#include "board_io.h"
#include "serial.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define CHECK(x) do { if (!(x)) { \
    fprintf(stderr, "hc11_bus_test:%d: %s\n", __LINE__, #x); exit(1); \
} } while (0)

typedef struct {
    uint8_t ram[0x400], external_gen[5], registers[0x60], board1[0x10], board2[0x40], rom[0x10];
    unsigned calls, failures, auth_calls, deny_auth;
    uint16_t last_address, last_value;
    unsigned last_width;
    char last_op;
    bool irq_masked, corrupt_failed_reads, lose_exclusive_on_read;
} Fake;

/* Only explicitly modeled target windows are provisioned; no 64K mirror. */
static uint8_t *cell(Fake *f, uint16_t a)
{
    if (a <= 0x03ffu) return &f->ram[a];
    if (a >= 0x080fu && a <= 0x0813u) return &f->external_gen[a-0x080fu];
    if (a >= 0x3000u && a <= 0x305fu) return &f->registers[a-0x3000u];
    if (a >= 0x3060u && a <= 0x306fu) return &f->board1[a-0x3060u];
    if (a >= 0x3fc0u && a <= 0x3fffu) return &f->board2[a-0x3fc0u];
    if (a >= 0x4000u && a <= 0x400fu) return &f->rom[a-0x4000u];
    return NULL;
}
static PcmStatus bus_call(Fake *f, char op, unsigned width,
                          uint16_t address, uint16_t value)
{
    f->calls++;
    if (f->calls == f->failures) return PCM_NO_HARDWARE;
    f->last_op=op;f->last_width=width;f->last_address=address;f->last_value=value;
    return PCM_OK;
}
static PcmStatus fake_read8(void *context, uint16_t a, uint8_t *v)
{
    Fake *f=context;uint8_t *p=cell(f,a);
    if (p==NULL || v==NULL) return PCM_BAD_CONFIGURATION;
    PcmStatus s=bus_call(f,'R',8,a,*p);
    if (s==PCM_OK) *v=*p;
    else if(f->corrupt_failed_reads) *v=0xee;
    if (f->lose_exclusive_on_read) f->irq_masked=false;
    return s;
}
static PcmStatus fake_read16(void *context, uint16_t a, uint16_t *v)
{
    Fake *f=context;
    uint8_t *hi=cell(f,a), *lo=cell(f,(uint16_t)(a+1u));
    if (a==0xffffu || hi==NULL || lo==NULL || v==NULL) return PCM_BAD_CONFIGURATION;
    uint16_t sample=(uint16_t)(((uint16_t)*hi<<8)|*lo);
    PcmStatus s=bus_call(f,'R',16,a,sample);
    if (s==PCM_OK) *v=sample;
    else if(f->corrupt_failed_reads) *v=0xdeadu;
    return s;
}
static PcmStatus fake_write8(void *context, uint16_t a, uint8_t v)
{
    Fake *f=context;uint8_t *p=cell(f,a);
    if(p==NULL) return PCM_BAD_CONFIGURATION;
    PcmStatus s=bus_call(f,'W',8,a,v);
    if(s==PCM_OK) *p=v;
    return s;
}
static PcmStatus fake_write16(void *context, uint16_t a, uint16_t v)
{
    Fake *f=context;
    uint8_t *hi=cell(f,a), *lo=cell(f,(uint16_t)(a+1u));
    if(a==0xffffu || hi==NULL || lo==NULL) return PCM_BAD_CONFIGURATION;
    PcmStatus s=bus_call(f,'W',16,a,v);
    if(s==PCM_OK) {*hi=(uint8_t)(v>>8);*lo=(uint8_t)v;}
    return s;
}
static PcmStatus fake_authorize(void *context,uint16_t a,
                                unsigned width,uint16_t v)
{
    Fake *f=context;(void)width;(void)v;
    ++f->auth_calls;
    return f->deny_auth || a==0x3067u ? PCM_NO_HARDWARE : PCM_OK;
}
static PcmStatus fake_irq(void *context,bool masked)
{
    Fake *f=context;f->irq_masked=masked;return PCM_OK;
}
static const PcmHc11Window windows[]={
    {0x0000,0x03ff,PCM_HC11_INTERNAL_RAM,PCM_HC11_R8|PCM_HC11_W8|PCM_HC11_R16|PCM_HC11_W16},
    {0x080f,0x0813,PCM_HC11_EXTERNAL_GEN,PCM_HC11_R8|PCM_HC11_W8|PCM_HC11_R16|PCM_HC11_W16},
    {0x3000,0x305f,PCM_HC11_CPU_REGISTERS,PCM_HC11_R8|PCM_HC11_W8|PCM_HC11_R16|PCM_HC11_W16},
    {0x3060,0x306f,PCM_HC11_BOARD_IO1,PCM_HC11_R8|PCM_HC11_W8|PCM_HC11_R16|PCM_HC11_W16},
    {0x3fc0,0x3fff,PCM_HC11_BOARD_IO2,PCM_HC11_R8|PCM_HC11_W8|PCM_HC11_R16|PCM_HC11_W16},
    {0x4000,0x400f,PCM_HC11_PROGRAM_IMAGE,PCM_HC11_R8|PCM_HC11_R16}
};
static void init(Fake *f,PcmHc11Bus *bus,PcmPlatform *platform,Pcm *pcm,
                 bool with_auth)
{
    memset(f,0,sizeof(*f));memset(bus,0,sizeof(*bus));
    memset(platform,0,sizeof(*platform));memset(pcm,0,sizeof(*pcm));
    PcmHc11Io io={0};
    io.context=f;
    io.read8=fake_read8;io.read16=fake_read16;
    io.write8=fake_write8;io.write16=fake_write16;
    io.mask_irq=fake_irq;
    if(with_auth) io.authorize_write=fake_authorize;
    CHECK(pcm_hc11_bus_bind(bus,platform,&io,windows,
                            sizeof(windows)/sizeof(windows[0]))==PCM_OK);
    pcm->platform=platform;
    CHECK(!platform->bind_fuel_ram_owners);
    CHECK(!platform->enable_resident_fuel_cycle);
    CHECK(platform->call_address==NULL);
}
static void test_regions_and_guard(void)
{
    static Fake f;PcmHc11Bus bus;PcmPlatform platform;Pcm p;
    init(&f,&bus,&platform,&p,false);
    CHECK(pcm_hc11_classify(0x0e00)==PCM_HC11_CONDITIONAL_EEPROM);
    CHECK(pcm_hc11_classify(0x1800)==PCM_HC11_EXTERNAL_GEN);
    CHECK(pcm_hc11_classify(0x3000)==PCM_HC11_CPU_REGISTERS);
    CHECK(pcm_hc11_classify(0x3060)==PCM_HC11_BOARD_IO1);
    CHECK(pcm_hc11_classify(0x3fce)==PCM_HC11_BOARD_IO2);
    CHECK(pcm_hc11_classify(0x4000)==PCM_HC11_PROGRAM_IMAGE);
    uint8_t value=0x5a;
    CHECK(pcm_read8(&p,0x0800,&value)==PCM_NO_HARDWARE);
    CHECK(pcm_read8(&p,0x1800,&value)==PCM_NO_HARDWARE && value==0x5a);
    CHECK(pcm_read8(&p,0x0f00,&value)==PCM_NO_HARDWARE);
    CHECK(pcm_read8(&p,0x2000,&value)==PCM_NO_HARDWARE);
    CHECK(pcm_write8(&p,0x3060,0x80)==PCM_NO_HARDWARE);
    CHECK(pcm_write16(&p,0x3fce,0x1234)==PCM_NO_HARDWARE);
    CHECK(f.calls==0 && f.board1[0]==0 && f.board2[0x0e]==0);
    CHECK(pcm_write8(&p,0x0004,0x32)==PCM_OK);
    CHECK(f.calls==1 && f.ram[4]==0x32);
    CHECK(pcm_write8(&p,0x4000,0xab)==PCM_NO_HARDWARE);
    CHECK(pcm_write16(&p,0x3fff,0x1234)==PCM_NO_HARDWARE);
    CHECK(pcm_read16(&p,0x306f,(uint16_t[1]){0})==PCM_NO_HARDWARE);
    CHECK(f.calls==1);
    CHECK(pcm_mask_irq(&p,true)==PCM_OK && f.irq_masked);
    CHECK(pcm_mask_irq(&p,false)==PCM_OK && !f.irq_masked);
    CHECK(pcm_read8(&p,0x3000,NULL)==PCM_BAD_CONFIGURATION);
}
static void test_width_and_raw_failure(void)
{
    static Fake f;PcmHc11Bus bus;PcmPlatform platform;Pcm p;
    init(&f,&bus,&platform,&p,true);
    f.board2[0x0e]=0x12;f.board2[0x0f]=0x34;
    uint16_t word=0;
    CHECK(pcm_read16(&p,0x3fce,&word)==PCM_OK && word==0x1234);
    CHECK(f.calls==1 && f.last_width==16 && f.last_op=='R');
    CHECK(pcm_write16(&p,0x3fce,0xabcd)==PCM_OK);
    CHECK(f.calls==2 && f.last_width==16 && f.last_address==0x3fce);
    CHECK(f.board2[0x0e]==0xab && f.board2[0x0f]==0xcd);
    CHECK(f.auth_calls==1);
    CHECK(pcm_write8(&p,0x3060,0x90)==PCM_OK);
    CHECK(f.calls==3 && f.last_width==8 && f.board1[0]==0x90);
    CHECK(pcm_write8(&p,0x3067,0x22)==PCM_NO_HARDWARE);
    CHECK(f.calls==3 && f.board1[7]==0);
    f.deny_auth=1;
    CHECK(pcm_write8(&p,PCM_COPRST,0x55)==PCM_NO_HARDWARE && f.calls==3);
    f.deny_auth=0;f.failures=4;
    CHECK(pcm_write16(&p,0x3fce,0x8888)==PCM_NO_HARDWARE);
    CHECK(f.calls==4 && f.board2[0x0e]==0xab && f.board2[0x0f]==0xcd);
    CHECK(pcm_read8(&p,0x4000,(uint8_t[1]){0})==PCM_OK);
}
static void test_canonical_ram_aliases(void)
{
    static Fake f;PcmHc11Bus bus;PcmPlatform platform;Pcm p;
    init(&f,&bus,&platform,&p,true);
    platform.bind_fuel_ram_owners=true; /* deliberate research opt-in */
    p.scheduler.run_counter=0x1122;
    f.ram[0xfd]=0x01;f.ram[0xfe]=0x02;
    uint16_t word;
    CHECK(pcm_read16(&p,0xfd,&word)==PCM_OK && word==0x1122);
    CHECK(f.calls==1 && f.last_width==16);
    CHECK(pcm_write16(&p,0xfd,0xbeef)==PCM_OK);
    CHECK(p.scheduler.run_counter==0xbeef);
    CHECK(f.ram[0xfd]==0xbe && f.ram[0xfe]==0xef);
    CHECK(pcm_write8(&p,0xfd,0x34)==PCM_OK);
    CHECK(p.scheduler.run_counter==0x34ef);
    f.failures=f.calls+1;
    CHECK(pcm_write16(&p,0xfd,0xaaaa)==PCM_NO_HARDWARE);
    CHECK(p.scheduler.run_counter==0x34ef);
    CHECK(f.ram[0xfd]==0x34 && f.ram[0xfe]==0xef);
    f.failures=0;
    p.runtime.spark_running=true;p.runtime.fuel_running=true;
    f.ram[0x4f]=0x02;uint8_t value;
    CHECK(pcm_read8(&p,0x4f,&value)==PCM_OK && value==0x92);
    CHECK(pcm_update8(&p,0x4f,0x80,0)==PCM_OK);
    CHECK(!p.runtime.spark_running && p.runtime.fuel_running);
    CHECK((f.ram[0x4f]&2u)!=0);
    p.io.vss_raw=0x1122u;
    CHECK(pcm_read16(&p,0x0812,&word)==PCM_OK && word==0x1122u);
    CHECK(pcm_write16(&p,0x0812,0x5678u)==PCM_OK);
    CHECK(p.io.vss_raw==0x5678u && f.external_gen[3]==0x56u &&
          f.external_gen[4]==0x78u);
    CHECK(pcm_write8(&p,0x0813,0x9au)==PCM_OK && p.io.vss_raw==0x569au);
}
static void test_window_validation(void)
{
    static Fake f;PcmHc11Bus bus;PcmPlatform platform;Pcm p;
    init(&f,&bus,&platform,&p,true);
    PcmHc11Io io=bus.io;
    PcmHc11Window bad[]={{0x3000,0x3060,PCM_HC11_CPU_REGISTERS,PCM_HC11_R8}};
    PcmPlatform clean={0};
    CHECK(pcm_hc11_bus_bind(&bus,&clean,&io,bad,1)==PCM_BAD_CONFIGURATION);
    PcmHc11Window overlap[]={
        {0x0000,0x001f,PCM_HC11_INTERNAL_RAM,PCM_HC11_R8},
        {0x001f,0x003f,PCM_HC11_INTERNAL_RAM,PCM_HC11_R8}
    };
    CHECK(pcm_hc11_bus_bind(&bus,&clean,&io,overlap,2)==PCM_BAD_CONFIGURATION);
    PcmHc11Window rom_write[]={
        {0x4000,0x400f,PCM_HC11_PROGRAM_IMAGE,PCM_HC11_W8}
    };
    CHECK(pcm_hc11_bus_bind(&bus,&clean,&io,rom_write,1)==PCM_BAD_CONFIGURATION);
    CHECK(pcm_hc11_bus_bind(&bus,&platform,&io,windows,
                            sizeof(windows)/sizeof(windows[0]))==PCM_BAD_CONFIGURATION);
    (void)p;
}
static void test_real_board_path_denied_tail(void)
{
    static Fake f;PcmHc11Bus bus;PcmPlatform platform;Pcm p;
    init(&f,&bus,&platform,&p,true);
    /* Exercise real F400..F41F source, not a synthetic bus-only write.
     * The 3067 authorization failure must preserve the successful prefix. */
    f.board1[0]=0x21;
    f.board1[4]=0xa5;
    p.spark.output_request=true;
    p.iac.kicker_request=false;
    p.transmission.output_shadow=0x5a;
    p.io.auxiliary_output=0x7b;
    f.irq_masked=true;
    CHECK(pcm_board_ports(&p)==PCM_NO_HARDWARE);
    CHECK(f.calls==4 && f.auth_calls==3);
    CHECK(f.board1[0]==0x10 && f.board1[2]==0x5a);
    CHECK(f.board1[7]==0);
    CHECK(p.io.output_context==0x21);
    CHECK(p.iac.input_shadow==0xa5);
    CHECK(f.irq_masked); /* failed path must not invent an early CLI */
}
static void test_mixed_word_via_bus(void)
{
    static Fake f;PcmHc11Bus bus;PcmPlatform platform;Pcm p;
    uint16_t word=0;
    init(&f,&bus,&platform,&p,true);
    platform.bind_fuel_ram_owners=true;
    /* A cross-owner 16-bit word must issue exactly one raw 16-bit bus
     * transaction, despite mixed flag and serial owners. */
    f.ram[0x41]=0x83;
    p.iac.park_neutral=true;
    p.fuel.ac_enrichment_seen=true;
    p.serial.sessions=0x5c;
    unsigned before_mixed=f.calls;
    CHECK(pcm_serial_memory_read16(&p,0x0041,&word)==PCM_OK &&
          word==0xab5c);
    CHECK(f.calls==before_mixed+1 && f.last_width==16);
    CHECK(pcm_write16(&p,0x0041,0x9277)==PCM_OK);
    CHECK(f.calls==before_mixed+2 && f.last_width==16);
    CHECK(f.ram[0x41]==0x92 && f.ram[0x42]==0x77 &&
          p.serial.sessions==0x77 && p.io.ac_mirror);

}
static void test_failed_reads_never_publish(void)
{
    static Fake f;PcmHc11Bus bus;PcmPlatform platform;Pcm p;
    init(&f,&bus,&platform,&p,true);
    f.corrupt_failed_reads=true;
    f.failures=1;
    uint8_t byte=0x76;
    CHECK(pcm_read8(&p,0x0004,&byte)==PCM_NO_HARDWARE && byte==0x76);
    f.failures=2;
    uint16_t word=0x2345;
    CHECK(pcm_read16(&p,0x00fd,&word)==PCM_NO_HARDWARE && word==0x2345);
    CHECK(f.calls==2);
}
static void test_aldl_logical_address_coherence(void)
{
    static Fake f;PcmHc11Bus bus;PcmPlatform platform;Pcm p;
    init(&f,&bus,&platform,&p,true);
    platform.bind_fuel_ram_owners=true;
    p.spark.vehicle_speed_high=0x3c;
    p.io.vehicle_speed_fraction=0x42;
    p.io.vss_raw=0x1122;
    p.io.output_context=0x21;
    p.spark.output_request=true;
    p.serial.descriptor=0xa55a;
    uint16_t word=0;uint8_t byte=0;
    CHECK(pcm_serial_memory_read16(&p,0x0284,&word)==PCM_OK && word==0x3c42);
    CHECK(pcm_serial_memory_read8(&p,0x004b,&byte)==PCM_OK && byte==0x31);
    CHECK(pcm_serial_memory_write8(&p,0x0812,0x9a)==PCM_OK &&
          p.io.vss_raw==0x9a22);
    CHECK(pcm_serial_memory_read16(&p,0x0812,&word)==PCM_OK && word==0x9a22);
    unsigned bus_calls=f.calls;
    CHECK(pcm_serial_memory_read16(&p,0x0362,&word)==PCM_OK && word==0xa55a);
    CHECK(pcm_serial_memory_write8(&p,0x0363,0x77)==PCM_OK &&
          p.serial.descriptor==0xa577);
    CHECK(f.calls==bus_calls); /* no second physical owner of serial RAM */
    CHECK(pcm_read16(&p,0x0362,&word)==PCM_OK && word==0xa577);
    CHECK(pcm_write8(&p,0x0362,0x44)==PCM_OK);
    CHECK(p.serial.descriptor==0x4477);
    CHECK(pcm_serial_memory_read16(&p,0x0362,&word)==PCM_OK && word==0x4477);
    CHECK(pcm_write8(&p,0x036c,0x82)==PCM_OK &&
          p.serial.receive[0]==0x82);
    CHECK(pcm_serial_memory_read8(&p,0x036c,&byte)==PCM_OK && byte==0x82);
}
static PcmStatus fake_exclusive(void *context)
{
    Fake *f=context;
    return f->irq_masked ? PCM_OK : PCM_NO_HARDWARE;
}
static void test_publish_explicit_internal_ram(void)
{
    static Fake f;PcmHc11Bus bus;PcmPlatform platform;Pcm p;
    init(&f,&bus,&platform,&p,true);
    platform.bind_fuel_ram_owners=true;
    PcmRamSyncGuard guard={&f,fake_exclusive};
    PcmRamSyncReport report={0};
    const PcmRamSyncEntry entries[]={
        {0x003au,1u,0x6fu}, /* partial owner; unknown flags retained */
        {0x0041u,1u,0x38u}, /* shared flags and residual */
        {0x0042u,1u,0xffu}, /* session byte */
        {0x00fdu,2u,0xffffu} /* run counter logical word */
    };
    p.scheduler.pending=true;
    p.runtime.adc_fault=true;
    p.iac.park_neutral=true;
    p.fuel.ac_enrichment_seen=true;
    p.serial.sessions=0x5au;
    p.scheduler.run_counter=0x1234u;
    f.ram[0x003a]=0x90u;f.ram[0x0041]=0x83u;
    f.ram[0x0042]=0x00u;
    f.ram[0x00fd]=0x11u;f.ram[0x00fe]=0x22u;
    CHECK(pcm_ram_sync_publish(&p,entries,4u,&guard,&report)==PCM_NO_HARDWARE);
    CHECK(f.calls==0 && report.written==0 && report.failed_index==0);
    CHECK(pcm_mask_irq(&p,true)==PCM_OK);
    CHECK(pcm_ram_sync_publish(&p,entries,4u,&guard,&report)==PCM_OK);
    CHECK(report.examined==4 && report.written==4 &&
          report.already_equal==0 && report.failed_index==4);
    CHECK(f.ram[0x003a]==0xb1u); /* original bits 7/4 preserved */
    CHECK(f.ram[0x0041]==0xabu);
    CHECK(f.ram[0x0042]==0x5au);
    CHECK(f.ram[0x00fd]==0x12u && f.ram[0x00fe]==0x34u);
    CHECK(f.irq_masked); /* no accidental CLI */
    unsigned before=f.calls;
    CHECK(pcm_ram_sync_publish(&p,entries,4u,&guard,&report)==PCM_OK);
    CHECK(report.written==0 && report.already_equal==4 &&
          f.calls==before+4);
    const PcmRamSyncEntry bad_mask[]={{0x0041u,1u,0x80u}};
    before=f.calls;
    CHECK(pcm_ram_sync_publish(&p,bad_mask,1u,&guard,&report)==PCM_BAD_CONFIGURATION);
    CHECK(f.calls==before);
    const PcmRamSyncEntry unknown[]={{0x0040u,1u,0xffu}};
    CHECK(pcm_ram_sync_publish(&p,unknown,1u,&guard,&report)==PCM_BAD_CONFIGURATION);
    const PcmRamSyncEntry bad_region[]={{0x3060u,1u,0xffu}};
    CHECK(pcm_ram_sync_publish(&p,bad_region,1u,&guard,&report)==PCM_NO_HARDWARE);
    const PcmRamSyncEntry external[]={{0x0812u,2u,0xffffu}};
    CHECK(pcm_ram_sync_publish(&p,external,1u,&guard,&report)==PCM_NO_HARDWARE);
    const PcmRamSyncEntry overlap[]={{0x0041u,2u,0xffffu},
                                     {0x0042u,1u,0xffu}};
    CHECK(pcm_ram_sync_publish(&p,overlap,2u,&guard,&report)==PCM_BAD_CONFIGURATION);
    CHECK(f.calls==before);
    CHECK(pcm_mask_irq(&p,false)==PCM_OK);
}

static void test_publish_fault_prefix_and_retry(void)
{
    static Fake f;PcmHc11Bus bus;PcmPlatform platform;Pcm p;
    init(&f,&bus,&platform,&p,true);
    platform.bind_fuel_ram_owners=true;
    PcmRamSyncGuard guard={&f,fake_exclusive};
    PcmRamSyncReport report={0};
    const PcmRamSyncEntry entries[]={
        {0x0042u,1u,0xffu},{0x00fdu,2u,0xffffu}
    };
    p.serial.sessions=0x91u;
    p.scheduler.run_counter=0xa5c3u;
    CHECK(pcm_mask_irq(&p,true)==PCM_OK);
    /* Call sequence: read8, write8, read16, [fail] write16.
     * First byte must remain committed, while word remains stale. */
    f.failures=4u;
    CHECK(pcm_ram_sync_publish(&p,entries,2u,&guard,&report)==PCM_NO_HARDWARE);
    CHECK(report.examined==2 && report.written==1 &&
          report.failed_index==1);
    CHECK(f.ram[0x0042]==0x91u && f.ram[0x00fd]==0x00u &&
          f.ram[0x00fe]==0x00u);
    CHECK(p.serial.sessions==0x91u && p.scheduler.run_counter==0xa5c3u);
    f.failures=0;
    CHECK(pcm_ram_sync_publish(&p,entries,2u,&guard,&report)==PCM_OK);
    CHECK(report.written==1 && report.already_equal==1);
    CHECK(f.ram[0x00fd]==0xa5u && f.ram[0x00fe]==0xc3u);
    /* Dirty failed read cannot result in a physical write. */
    f.corrupt_failed_reads=true;
    f.failures=f.calls+1;
    p.serial.sessions=0x7bu;
    CHECK(pcm_ram_sync_publish(&p,entries,2u,&guard,&report)==PCM_NO_HARDWARE);
    CHECK(report.written==0 && f.ram[0x0042]==0x91u);
    CHECK(pcm_mask_irq(&p,false)==PCM_OK);
}
static void test_publish_guard_lost_after_physical_read(void)
{
    static Fake f;PcmHc11Bus bus;PcmPlatform platform;Pcm p;
    init(&f,&bus,&platform,&p,true);
    platform.bind_fuel_ram_owners=true;
    PcmRamSyncGuard guard={&f,fake_exclusive};
    PcmRamSyncReport report={0};
    const PcmRamSyncEntry entry={0x0042u,1u,0xffu};
    p.serial.sessions=0x7au;
    CHECK(pcm_mask_irq(&p,true)==PCM_OK);
    f.lose_exclusive_on_read=true;
    CHECK(pcm_ram_sync_publish(&p,&entry,1u,&guard,&report)==PCM_NO_HARDWARE);
    CHECK(f.calls==1 && f.ram[0x0042]==0u && !f.irq_masked);
    CHECK(report.examined==1 && report.written==0 && report.failed_index==0);
}
static void test_native_is_fail_closed_on_host(void)
{
#ifndef PCM_HC11_NATIVE_MMIO
    PcmHc11Io native={0};
    pcm_hc11_native_mmio_init(&native,NULL,NULL);
    uint8_t value=0xc4;
    CHECK(native.read8(native.context,0x3000,&value)==PCM_NO_HARDWARE);
    CHECK(value==0xc4);
    CHECK(native.write8(native.context,0x3060,0xff)==PCM_NO_HARDWARE);
#endif
}
int main(void)
{
    test_regions_and_guard();test_width_and_raw_failure();
    test_canonical_ram_aliases();test_window_validation();
    test_real_board_path_denied_tail();
    test_failed_reads_never_publish();
    test_mixed_word_via_bus();
    test_publish_explicit_internal_ram();
    test_publish_fault_prefix_and_retry();
    test_publish_guard_lost_after_physical_read();
    test_aldl_logical_address_coherence();
    test_native_is_fail_closed_on_host();
    puts("HC11 mapped bus: explicit grants, fail-closed hardware writes, word width, RAM owners and failure prefixes passed.");
    return 0;
}
