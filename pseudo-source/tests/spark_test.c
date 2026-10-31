#include "spark.h"
#include "reference_math.h"
#include "calibration.h"
#include "hardware.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CHECK(x) do { if (!(x)) { fprintf(stderr,"Spark check failed at %d: %s\n",__LINE__,#x);exit(1); } } while (0)
typedef struct { uint16_t address; uint8_t width,mask,count;size_t offset; } Mapping;
#define B(a,m) {a,8,0,1,offsetof(Pcm,m)}
#define W(a,m) {a,16,0,1,offsetof(Pcm,m)}
#define F(a,b,m) {a,0,b,1,offsetof(Pcm,m)}
static const Mapping state_map[]={
    B(0x06,reference.coolant),F(0x19,0x10,knock.sensor_fault),F(0x3d,0x20,runtime.power_enrichment),
    F(0x41,0x02,spark.mat_negative),F(0x50,0x40,spark.idle_feedback),F(0x50,0x80,spark.idle_state),
    B(0x61,spark.rpm_low_coordinate),B(0x62,reference.rpm_coordinate),F(0x6e,0x80,spark.egr_active),
    B(0x6f,spark.load_status),B(0xa4,spark.transmission_status),B(0x15a,spark.transmission_retard),
    B(0x1b2,spark.egr_fraction_high),B(0x1c0,spark.load_coordinate),B(0x1c1,spark.recent_load),
    B(0x1c2,spark.previous_load),B(0x1c9,spark.vacuum),B(0x1cc,spark.barometric_pressure),
    W(0x1f4,spark.egr_filtered),B(0x1f8,spark.base_advance),B(0x1f9,spark.coolant_advance),
    B(0x1fa,spark.mat_magnitude),B(0x1fb,spark.altitude_advance),B(0x1fc,spark.pe_advance),
    W(0x1fd,spark.composite),B(0x20a,knock.scaled_activity),B(0x20b,knock.adaptive_retard),
    B(0x22f,spark.mat_sample),B(0x278,spark.pe_fraction),B(0x2cb,spark.startup_adder),
    B(0x83c,spark.mat_effect),B(0x841,knock.octane_rpm_factor),B(0x843,knock.event_gain),B(0x844,knock.retard_limit),
    B(0x63,spark.rpm_high),B(0x64,spark.rpm_fraction),B(0x6c,spark.idle_derivative),W(0xfd,scheduler.run_counter),
    F(0x46,0x08,runtime.deceleration_fuel_cut),F(0x51,0x20,spark.recovery_active),F(0x53,0x01,spark.idle_negative),
    B(0x1d9,reference.throttle),W(0x1f2,spark.startup_recovery_gain),B(0x208,spark.decel_retard),
    B(0x837,spark.transient_target),W(0x838,spark.transient_filtered),B(0x83a,spark.transient_error),
    B(0x83b,spark.transient_correction),B(0x857,spark.iac_desired_speed),B(0x284,spark.vehicle_speed_high),
    F(0x86,0x40,scheduler.profiling_enabled),F(0x36,0x20,spark.override_request),F(0x53,0x10,spark.override_active),
    F(0x3b,0x10,runtime.engine_service),B(0x395,spark.service_flags),B(0x398,spark.service_amount),
    W(0x1ee,spark.command),W(0x1f0,spark.command_latched),B(0x16,runtime.primary_faults),
    F(0x50,0x10,runtime.diagnostic_switch),F(0x6e,0x02,knock.burst_active),B(0x1da,spark.previous_throttle),
    B(0x20c,knock.retard),B(0x20d,knock.observation_accumulator),B(0x20e,knock.burst_countdown),B(0x842,knock.burst_gain),
    B(0x02,scheduler.phase),W(0x83d,spark.rpm_raw),W(0x28e,spark.rpm_monitor_filtered),
    B(0x28c,spark.rpm_monitor_previous),B(0x28d,spark.rpm_monitor_delta),B(0x67,reference.load_coordinate),
    W(0x68,reference.load_filtered),W(0x1e8,spark.period),W(0x1e6,spark.previous_period),
    W(0x83f,spark.reference_term),W(0x1ec,spark.period_correction),B(0xa7,spark.battery_sample),
    B(0x1c6,spark.map_filtered),B(0x2f4,spark.barometric_high),B(0x1ce,spark.normalized_load_divisor),
    W(0x257,spark.density),B(0x1cf,spark.normalized_load),B(0x229,spark.map_fault_count),F(0x18,0x10,spark.map_fault),
    B(0x82e,reference.map_sample),F(0x50,0x20,reference.pending),F(0x50,0x04,reference.consumed),
    F(0x4f,0x10,runtime.fuel_running),F(0x4f,0x80,runtime.spark_running),F(0x4f,0x40,spark.startup_gain_enabled),
    F(0x44,0x08,spark.first_reference),F(0x51,0x40,spark.startup_gain_complete),F(0x04,0x08,spark.run_transition),
    B(0x211,spark.fuel_run_count),B(0x210,spark.spark_run_count),B(0x202,spark.missing_reference_count),
    W(0x260,spark.reference_age),W(0x1ea,spark.adaptive_period),W(0x5f,spark.period_basis),B(0x2ce,reference.event_age),
    F(0x4f,0x01,spark.command_negative),F(0x4b,0x10,spark.output_request),B(0x201,spark.output_latency)
};
#undef B
#undef W
#undef F
#define B(a,m) {a,8,0,1,offsetof(PcmCalibration,m)}
#define A(a,n,m) {a,8,0,n,offsetof(PcmCalibration,m)}
static const Mapping root_map[]={
    B(0x400b,reference.mode_b),B(0x400d,mode_d),B(0x400f,mode_f),B(0x45da,knock.minimum_coolant),
    A(0x4585,8,knock.pe_retard_cap),A(0x458d,7,knock.cruise_retard_cap),
    A(0x4594,17,knock.event_gain_curve),A(0x45be,9,knock.octane_rpm),A(0x45c7,17,knock.octane_load),
    B(0x45d8,knock.minimum_speed),B(0x45d9,knock.minimum_rpm_high),B(0x4e77,knock.fault_retard),
    B(0x46df,knock.burst_load_limit),B(0x46e0,knock.burst_throttle_limit),B(0x46e1,knock.burst_throttle_delta),
    B(0x46e2,knock.burst_duration),B(0x48da,reference.throttle_limit)
};
#undef B
#undef A
#define B(a,m) {a,8,0,1,offsetof(PcmSparkCalibration,m)}
#define A(a,n,m) {a,8,0,n,offsetof(PcmSparkCalibration,m)}
#define W(a,m) {a,16,0,1,offsetof(PcmSparkCalibration,m)}
static const Mapping spark_map[]={
    B(0x43ae,coolant_mode),B(0x4439,mat_mode),B(0x485f,egr_mode),B(0x485e,egr_gain),
    B(0x413b,base_bias),B(0x413c,coolant_bias),B(0x413d,altitude_bias),B(0x413e,egr_bias),
    B(0x413f,mat_bias),B(0x4140,idle_coolant_threshold),B(0x55f2,transmission_bias),
    A(0x449d,17,mat_negative_gain),A(0x44ae,17,mat_positive_gain),A(0x44bf,17,pe_curve),
    B(0x415a,idle_speed_limit),B(0x415b,idle_throttle_entry),B(0x415c,idle_throttle_retained),
    B(0x415d,idle_coolant_minimum),W(0x415e,idle_runtime_minimum),B(0x4160,idle_target_adder),
    B(0x4514,idle_bias),B(0x4515,idle_positive_cap),A(0x451b,17,idle_derivative_curve),
    B(0x46f2,transient_coolant_minimum),B(0x46f3,transient_coolant_maximum),A(0x46f4,5,transient_gain),
    A(0x46ec,3,transient_positive),A(0x46ef,3,transient_negative),B(0x414f,recovery_gain),
    B(0x4150,recovery_fast_gain),B(0x4151,recovery_throttle),B(0x4152,decel_base),
    B(0x4132,reference_bias),B(0x4e90,override_options),B(0x4161,override_coolant_minimum),
    B(0x4164,override_throttle_entry),B(0x4165,override_throttle_retained),W(0x4162,override_command),
    W(0x4144,upper_limit),W(0x4146,lower_normal),W(0x4148,lower_recovery),
    W(0x414a,lower_transmission),W(0x414c,lower_transmission_state),
    B(0x4141,period_scale),B(0x4153,rpm_filter_gain),B(0x4517,load_filter_gain),B(0x50e4,monitor_filter_gain),
    W(0x4133,spark_run_period_limit),W(0x4135,fuel_run_period_limit),W(0x4962,no_reference_age_limit),
    B(0x4142,spark_run_events),B(0x4143,fuel_run_events),B(0x414e,startup_gain),
    B(0x4e64,map_sample_minimum),B(0x4e65,map_rpm_minimum),B(0x4e66,map_count_limit),
    B(0x4e67,map_throttle_limit),B(0x4d96,missing_reference_age_cap)
};
#undef B
#undef A
#undef W
typedef struct { uint16_t address,capacity;size_t offset; } TableMapping;
#define T(a,n,m) {a,n,offsetof(PcmSparkCalibration,m)}
static const TableMapping tables[]={T(0x4166,289,base_normal),T(0x428a,289,base_idle),
    T(0x43af,144,coolant),T(0x44d5,66,altitude),T(0x443a,109,mat),T(0x4860,79,egr)};
static const TableMapping curves[]={T(0x44f0,8,idle_negative_speed),T(0x44f8,10,idle_negative_load),
    T(0x4502,8,idle_positive_speed),T(0x450a,10,idle_positive_load),T(0x454a,14,output_latency)};
#undef T
typedef struct { char kind;uint8_t width;uint16_t address,value;bool masked; } Event;
typedef struct {
    uint8_t memory[65536],present[65536],data[6][527],curve_data[5][17];
    Event events[32];unsigned used,attempts,fail_at,action;bool masked;
    uint16_t periods[16],partial;unsigned read_count,read_index;Pcm *pcm;
    bool real_alternate;uint8_t coordinate_low,coordinate_rounded;
    PcmPlatform platform;
} Fixture;
static uint16_t word(const uint8_t *m,uint16_t a)
{ return (uint16_t)((uint16_t)m[a]*256u+m[(uint16_t)(a+1u)]); }
static void transfer(void *object,uint8_t *memory,const Mapping *map,size_t count,bool load)
{
    for (size_t i=0;i<count;++i) {
        const Mapping *m=&map[i];uint8_t *field=(uint8_t *)object+m->offset;
        if (m->mask) {
            volatile bool *value=(volatile bool *)(void *)field;
            if (load) *value=(memory[m->address]&m->mask)!=0;
            else memory[m->address]=(uint8_t)((memory[m->address]&(uint8_t)~m->mask)|(*value?m->mask:0));
        } else if (m->width==16) {
            volatile uint16_t *value=(volatile uint16_t *)(void *)field;
            if (load) *value=word(memory,m->address);
            else { memory[m->address]=(uint8_t)(*value>>8);memory[m->address+1]=(uint8_t)*value; }
        } else for (unsigned j=0;j<m->count;++j) {
            volatile uint8_t *value=field+j;
            if (load) *value=memory[m->address+j];else memory[m->address+j]=*value;
        }
    }
}
static void put(Fixture *f,unsigned address,uint8_t value)
{
    CHECK(!f->present[address] || f->memory[address]==value);
    f->present[address]=1;f->memory[address]=value;
}
static void defaults(Fixture *f,PcmCalibration *root,PcmSparkCalibration *spark)
{
    for (size_t t=0;t<6;++t) {
        const TableMapping *map=&tables[t];
        const PcmTable2D *v=(const PcmTable2D *)(const void *)((const uint8_t *)spark+map->offset);
        CHECK(v->length==map->capacity);
        put(f,map->address,v->row_offset);put(f,map->address+1,v->column_offset);put(f,map->address+2,v->stride);
        for (unsigned i=0;i<v->length;++i) put(f,map->address+3+i,v->values[i]);
    }
    for (unsigned group=0;group<2;++group) {
        const Mapping *map=group?spark_map:root_map;
        size_t count=group?sizeof(spark_map)/sizeof(spark_map[0]):sizeof(root_map)/sizeof(root_map[0]);
        const uint8_t *object=group?(const uint8_t *)spark:(const uint8_t *)root;
        for (size_t i=0;i<count;++i) {
            if (map[i].width==16) {
                uint16_t value=*(const uint16_t *)(const void *)(object+map[i].offset);
                put(f,map[i].address,(uint8_t)(value>>8));put(f,map[i].address+1,(uint8_t)value);
            } else for (unsigned j=0;j<map[i].count;++j) put(f,map[i].address+j,object[map[i].offset+j]);
        }
    }
    for (unsigned i=0;i<5;++i) {
        const TableMapping *map=&curves[i];
        const PcmCappedCurve *v=(const PcmCappedCurve *)(const void *)((const uint8_t *)spark+map->offset);
        CHECK(v->length==map->capacity);put(f,map->address,v->limit);
        for (unsigned j=0;j<v->length;++j) put(f,map->address+1+j,v->values[j]);
    }
}
static void init(Fixture *f,Pcm *pcm,PcmCalibration *root,PcmSparkCalibration *spark)
{
    memset(f,0,sizeof(*f));memset(pcm,0,sizeof(*pcm));
    *root=pcm_reference_scheduler_calibration;*spark=pcm_reference_spark_calibration;
    root->spark=spark;pcm->calibration=root;pcm->unresolved_task=PCM_TASK_COUNT;
    defaults(f,root,spark);
    for (unsigned i=0;i<527;++i) f->memory[0x6003+i]=(uint8_t)(i*73u+(i>>2)*19u+41u);
    f->memory[0x6002]=17;f->memory[0x5ffe]=2;f->memory[0x5fff]=15; /* length527 */
    f->memory[0x6300]=128;f->memory[0x905]=17;
    for (unsigned i=0;i<17;++i) f->memory[0x6301+i]=(uint8_t)(i*73u+(i>>2)*19u+41u);
}
static void load_cal(Fixture *f,PcmCalibration *root,PcmSparkCalibration *spark)
{
    transfer(root,f->memory,root_map,sizeof(root_map)/sizeof(root_map[0]),true);
    transfer(spark,f->memory,spark_map,sizeof(spark_map)/sizeof(spark_map[0]),true);
    for (unsigned i=0;i<6;++i) {
        const TableMapping *map=&tables[i];PcmTable2D *v=(PcmTable2D *)(void *)((uint8_t *)spark+map->offset);
        v->row_offset=f->memory[map->address];v->column_offset=f->memory[map->address+1];v->stride=f->memory[map->address+2];
        v->values=f->data[i];memcpy(f->data[i],f->memory+map->address+3,map->capacity);
    }
    for (unsigned i=0;i<5;++i) {
        const TableMapping *map=&curves[i];PcmCappedCurve *v=(PcmCappedCurve *)(void *)((uint8_t *)spark+map->offset);
        v->limit=f->memory[map->address];v->values=f->curve_data[i];
        /* Test-only profile expansion exposes coordinates hidden by stock caps. */
        v->length=f->memory[0x906]?17:(uint8_t)map->capacity;
        memcpy(f->curve_data[i],f->memory+map->address+1,v->length);
    }
}
static PcmStatus record(Fixture *f,char kind,uint8_t width,uint16_t address,uint16_t value)
{
    if (++f->attempts==f->fail_at) return PCM_NO_HARDWARE;
    CHECK(f->used<32);f->events[f->used++]=(Event){kind,width,address,value,f->masked};return PCM_OK;
}
static PcmStatus mask(void *context,bool masked)
{
    Fixture *f=context;PcmStatus result=record(f,'M',0,0,masked);
    if (result==PCM_OK) {
        f->masked=masked;
        if (!masked && f->action==4) { f->pcm->reference.pending=true;f->pcm->runtime.spark_running=true; }
    }
    return result;
}
static PcmStatus extension(Pcm *pcm,PcmTask task)
{
    CHECK(task==PCM_SPARK_EXTENSION || task==PCM_SPARK_OUTPUT_EXTENSION);Fixture *f=pcm->platform->context;
    PcmStatus result=record(f,'T',0,task==PCM_SPARK_EXTENSION?0x1812:0x180f,
                            task==PCM_SPARK_EXTENSION?(uint16_t)f->action:pcm->spark.extension_magnitude);
    if (result!=PCM_OK) return result;
    if (task==PCM_SPARK_OUTPUT_EXTENSION) {
        if (f->action==6) {
            pcm->spark.extension_magnitude^=0xa5;pcm->spark.command_negative=true;
            pcm->reference.rpm_coordinate=0xc1;pcm->spark.period_basis=0xff80;
        }
        return PCM_OK;
    }
    if (f->action==1) { pcm->spark.composite=0x8123;pcm->scheduler.profiling_enabled=false; }
    else if (f->action==2) {
        pcm->spark.override_request=true;pcm->spark.override_active=true;
        pcm->reference.coolant=255;pcm->reference.throttle=7;
    }
    return PCM_OK;
}
static PcmStatus read8(void *context,uint16_t address,uint8_t *value)
{
    Fixture *f=context;CHECK(address==PCM_BOARD_3060);
    uint8_t sample=f->memory[address];PcmStatus result=record(f,'R',8,address,sample);
    if (result==PCM_OK) *value=sample;
    return result;
}
static PcmStatus read16(void *context,uint16_t address,uint16_t *value)
{
    Fixture *f=context;CHECK(address==PCM_REFERENCE_PERIOD || address==PCM_SPARK_ROLLING || address==PCM_SPARK_WORD);
    uint16_t sample=word(f->memory,address);
    if (f->read_count) { CHECK(f->read_index<f->read_count);sample=f->periods[f->read_index++]; }
    PcmStatus result=record(f,'R',16,address,sample);
    if (result==PCM_OK) {
        *value=sample;
        if (f->action==3) f->pcm->spark.period_correction=0xffff;
        if (f->action==9 && address==PCM_SPARK_WORD) f->pcm->spark.period_correction=0x9abc;
    }
    return result;
}
static PcmStatus write8(void *context,uint16_t address,uint8_t value)
{
    Fixture *f=context;CHECK(address==PCM_BOARD_3060 || address==PCM_REFERENCE_AGE);
    PcmStatus result=record(f,'W',8,address,value);
    if (result==PCM_OK) f->memory[address]=value;
    return result;
}
static PcmStatus alternate(Pcm *pcm,PcmTask task)
{
    CHECK(task==PCM_ALTERNATE_RPM);Fixture *f=pcm->platform->context;
    if (f->real_alternate) return pcm_spark_alternate(pcm);
    PcmStatus result=record(f,'T',0,0xac51,(uint16_t)f->action);
    if (result==PCM_OK && f->action==5) {
        pcm->reference.consumed=false;pcm->spark.period_basis=0xffff;pcm->spark.rpm_low_coordinate=0x77;
    }
    return result;
}
static PcmStatus write16(void *context,uint16_t address,uint16_t value)
{
    Fixture *f=context;
    CHECK(address==PCM_SPARK_TIMING_A || address==PCM_SPARK_TIMING_B || address==PCM_SPARK_WORD || address==PCM_SPARK_ROLLING);
    PcmStatus result=record(f,'W',16,address,value);
    if (result==PCM_OK) {
        f->memory[address]=(uint8_t)(value>>8);f->memory[address+1u]=(uint8_t)value;
        if (f->action==7 && address==PCM_SPARK_TIMING_B) f->pcm->spark.period_correction=0x1234;
        if (f->action==8 && address==PCM_SPARK_TIMING_A) f->pcm->spark.period_correction=0x5678;
    }
    return result;
}
static void bind(Fixture *f,Pcm *pcm)
{
    f->pcm=pcm;f->platform.read8=read8;f->platform.read16=read16;f->platform.write8=write8;f->platform.write16=write16;
    f->platform.context=f;f->platform.mask_irq=mask;f->platform.task[PCM_SPARK_EXTENSION]=extension;
    f->platform.task[PCM_SPARK_OUTPUT_EXTENSION]=extension;
    f->platform.task[PCM_ALTERNATE_RPM]=alternate;
    pcm->platform=&f->platform;
}
static void contracts(void)
{
    static Fixture f;Pcm pcm;PcmCalibration root;PcmSparkCalibration spark;
    const PcmRoutine routines[]={pcm_spark_base,pcm_spark_coolant,pcm_spark_altitude,pcm_spark_egr,
        pcm_spark_sum,pcm_spark_mat_effect,pcm_spark_mat,pcm_spark_pe,pcm_spark_auxiliary,pcm_spark_terms};
    for (unsigned i=0;i<10;++i) {
        init(&f,&pcm,&root,&spark);pcm.calibration=NULL;CHECK(routines[i](&pcm)==PCM_BAD_CONFIGURATION);
        init(&f,&pcm,&root,&spark);root.spark=NULL;CHECK(routines[i](&pcm)==PCM_BAD_CONFIGURATION);
        init(&f,&pcm,&root,&spark);CHECK(routines[i](&pcm)==PCM_OK); /* Pure source: no platform binding. */
    }
    uint8_t result=222,values[527]={0};PcmTable2D table={0,0,17,527,values};
    CHECK(pcm_lookup2d(0,0,NULL,&result)==PCM_BAD_CONFIGURATION && result==222);
    CHECK(pcm_lookup2d(0,0,&table,NULL)==PCM_BAD_CONFIGURATION);
    table.values=NULL;CHECK(pcm_lookup2d(0,0,&table,&result)==PCM_BAD_CONFIGURATION && result==222);
    table.values=values;table.length=18;CHECK(pcm_lookup2d(0,0,&table,&result)==PCM_BAD_CONFIGURATION && result==222);
    table.length=19;CHECK(pcm_lookup2d(0,0,&table,&result)==PCM_OK); /* Includes zero-weight neighbors. */
    init(&f,&pcm,&root,&spark);spark.base_normal.values=NULL;
    pcm.spark.load_coordinate=33;pcm.spark.recent_load=22;pcm.spark.previous_load=11;pcm.spark.base_advance=77;
    CHECK(pcm_spark_base(&pcm)==PCM_BAD_CONFIGURATION);
    CHECK(pcm.spark.previous_load==22 && pcm.spark.recent_load==33 && pcm.spark.base_advance==77);
    init(&f,&pcm,&root,&spark);spark.coolant.length=0;
    pcm.spark.load_coordinate=33;pcm.spark.recent_load=22;pcm.spark.coolant_advance=77;pcm.spark.composite=0x1234;
    CHECK(pcm_spark_terms(&pcm)==PCM_BAD_CONFIGURATION);
    CHECK(pcm.spark.previous_load==22 && pcm.spark.recent_load==33 && pcm.spark.coolant_advance==77 && pcm.spark.composite==0x1234);
    init(&f,&pcm,&root,&spark);spark.mat.values=NULL;pcm.spark.mat_negative=true;pcm.spark.mat_magnitude=77;
    CHECK(pcm_spark_mat(&pcm)==PCM_OK && pcm.spark.mat_negative && pcm.spark.mat_magnitude==0);
    root.reference.mode_b|=0x40;pcm.spark.mat_sample=80;pcm.spark.mat_magnitude=77;
    CHECK(pcm_spark_auxiliary(&pcm)==PCM_BAD_CONFIGURATION && pcm.spark.mat_magnitude==77);
    init(&f,&pcm,&root,&spark);spark.altitude.values=NULL;pcm.spark.altitude_advance=77;
    CHECK(pcm_spark_altitude(&pcm)==PCM_OK && pcm.spark.altitude_advance==77);
    root.mode_d|=4;CHECK(pcm_spark_altitude(&pcm)==PCM_BAD_CONFIGURATION && pcm.spark.altitude_advance==77);
    init(&f,&pcm,&root,&spark);spark.egr.values=NULL;spark.egr_bias=23;
    CHECK(pcm_spark_egr(&pcm)==PCM_OK && pcm.spark.egr_filtered==0x1700);
    pcm.spark.egr_active=true;CHECK(pcm_spark_egr(&pcm)==PCM_BAD_CONFIGURATION && pcm.spark.egr_filtered==0x1700);
    puts("Spark calibration, matrix bounds, retained routes and failure-prefix contracts pass.");
}
static void modifier_contracts(void)
{
    static Fixture f;Pcm pcm;PcmCalibration root;PcmSparkCalibration spark;
    const PcmRoutine routines[]={pcm_spark_idle,pcm_spark_transient,pcm_spark_decel,pcm_spark_modifiers,pcm_spark_composite};
    for (unsigned i=0;i<5;++i) {
        init(&f,&pcm,&root,&spark);pcm.calibration=NULL;CHECK(routines[i](&pcm)==PCM_BAD_CONFIGURATION);
        init(&f,&pcm,&root,&spark);root.spark=NULL;CHECK(routines[i](&pcm)==PCM_BAD_CONFIGURATION);
        init(&f,&pcm,&root,&spark);CHECK(routines[i](&pcm)==PCM_OK);
    }
    uint8_t values[17]={0},result=222;PcmCappedCurve curve={255,17,values};
    CHECK(pcm_lookup_capped(0,NULL,&result)==PCM_BAD_CONFIGURATION && result==222);
    CHECK(pcm_lookup_capped(0,&curve,NULL)==PCM_BAD_CONFIGURATION);
    curve.values=NULL;CHECK(pcm_lookup_capped(0,&curve,&result)==PCM_BAD_CONFIGURATION && result==222);
    curve.values=values;curve.length=1;CHECK(pcm_lookup_capped(0,&curve,&result)==PCM_BAD_CONFIGURATION && result==222);
    curve.length=8;curve.limit=112;CHECK(pcm_lookup_capped(255,&curve,&result)==PCM_BAD_CONFIGURATION && result==222);
    curve.limit=96;CHECK(pcm_lookup_capped(255,&curve,&result)==PCM_OK);
    init(&f,&pcm,&root,&spark);pcm.reference.coolant=200;pcm.spark.idle_feedback=true;
    pcm.spark.rpm_high=1;pcm.spark.composite=0x1234;spark.idle_negative_speed.values=NULL;
    CHECK(pcm_spark_idle(&pcm)==PCM_BAD_CONFIGURATION && pcm.spark.idle_negative && pcm.spark.idle_feedback);
    CHECK(pcm.spark.composite==0x1234);
    pcm.reference.throttle=255;CHECK(pcm_spark_idle(&pcm)==PCM_OK && !pcm.spark.idle_feedback && pcm.spark.idle_negative);
    init(&f,&pcm,&root,&spark);pcm.reference.coolant=200;pcm.spark.rpm_high=1;spark.idle_negative_speed.values=NULL;
    CHECK(pcm_spark_composite(&pcm)==PCM_BAD_CONFIGURATION);
    CHECK(pcm.spark.recent_load==0 && pcm.spark.coolant_advance!=0 && pcm.spark.idle_negative);
    puts("Modifier calibration, capped-curve bounds, idle retention and prefix contracts pass.");
}
static void command_contracts(void)
{
    static Fixture f;Pcm pcm;PcmCalibration root;PcmSparkCalibration spark;
    const PcmRoutine routines[]={pcm_spark_override,pcm_spark_upper_limit,pcm_spark_lower_limit};
    for (unsigned i=0;i<3;++i) {
        init(&f,&pcm,&root,&spark);pcm.calibration=NULL;CHECK(routines[i](&pcm)==PCM_BAD_CONFIGURATION);
        init(&f,&pcm,&root,&spark);root.spark=NULL;CHECK(routines[i](&pcm)==PCM_BAD_CONFIGURATION);
        init(&f,&pcm,&root,&spark);CHECK(routines[i](&pcm)==PCM_OK);
    }
    init(&f,&pcm,&root,&spark);pcm.calibration=NULL;CHECK(pcm_spark_service(&pcm)==PCM_OK);
    CHECK(pcm_spark_extension(&pcm)==PCM_OK);
    pcm.scheduler.profiling_enabled=true;pcm.spark.command=0x1234;
    CHECK(pcm_spark_extension(&pcm)==PCM_UNIMPLEMENTED && pcm.unresolved_task==PCM_SPARK_EXTENSION);
    CHECK(pcm.spark.command==0x1234);
    init(&f,&pcm,&root,&spark);bind(&f,&pcm);pcm.scheduler.profiling_enabled=true;
    f.action=1;f.fail_at=2;pcm.knock.observation_accumulator=73;pcm.spark.command_latched=0x3333;
    CHECK(pcm_spark_command(&pcm)==PCM_NO_HARDWARE);
    CHECK(pcm.spark.composite==0x8123 && !pcm.scheduler.profiling_enabled && pcm.spark.command==0x8118);
    CHECK(pcm.knock.observation_accumulator==73 && pcm.spark.command_latched==0x3333);
    init(&f,&pcm,&root,&spark);bind(&f,&pcm);f.fail_at=2;pcm.knock.observation_accumulator=73;
    CHECK(pcm_spark_command(&pcm)==PCM_NO_HARDWARE && pcm.knock.observation_accumulator==0 && f.masked);
    init(&f,&pcm,&root,&spark);pcm.scheduler.profiling_enabled=true;
    CHECK(pcm_spark_calculate(&pcm)==PCM_UNIMPLEMENTED && pcm.unresolved_task==PCM_SPARK_EXTENSION);
    CHECK(pcm.spark.coolant_advance!=0 && pcm.spark.command_latched==0);
    puts("Command calibration, inactive/unbound extension and failure-prefix contracts pass.");
}
static void period_contracts(void)
{
    static Fixture f;Pcm pcm;PcmCalibration root;PcmSparkCalibration spark;
    const PcmRoutine routines[]={pcm_spark_period_sample,pcm_spark_rpm_filters,pcm_spark_precompute};
    for (unsigned i=0;i<3;++i) {
        init(&f,&pcm,&root,&spark);pcm.calibration=NULL;CHECK(routines[i](&pcm)==PCM_BAD_CONFIGURATION);
        init(&f,&pcm,&root,&spark);root.spark=NULL;CHECK(routines[i](&pcm)==PCM_BAD_CONFIGURATION);
    }
    init(&f,&pcm,&root,&spark);pcm.spark.period=77;pcm.spark.period_basis=88;
    CHECK(pcm_spark_period_sample(&pcm)==PCM_NO_HARDWARE && pcm.spark.period==77 && pcm.spark.period_basis==88);
    init(&f,&pcm,&root,&spark);pcm.spark.period=2000;pcm.spark.previous_period=2100;
    CHECK(pcm_spark_period_terms(&pcm)==PCM_NO_HARDWARE && pcm.spark.previous_period==2000 && pcm.spark.reference_term!=0);
    init(&f,&pcm,&root,&spark);bind(&f,&pcm);pcm.calibration=NULL;pcm.spark.period=2000;
    CHECK(pcm_spark_period_terms(&pcm)==PCM_OK);
    init(&f,&pcm,&root,&spark);pcm.spark.rpm_raw=12345;pcm.reference.rpm_coordinate=99;
    spark.rpm_filter_gain=spark.load_filter_gain=0;CHECK(pcm_spark_rpm_filters(&pcm)==PCM_OK);
    CHECK(pcm.spark.rpm_high==96 && pcm.spark.rpm_fraction==114 && pcm.reference.load_filtered!=0);
    pcm.spark.rpm_monitor_filtered=0xff80;pcm.scheduler.phase=4;pcm.spark.rpm_monitor_previous=255;
    CHECK(pcm_spark_rpm_filters(&pcm)==PCM_OK && pcm.spark.rpm_monitor_previous==0 && pcm.spark.rpm_monitor_delta==1);
    bool built=true;init(&f,&pcm,&root,&spark);CHECK(pcm_spark_build(&pcm,NULL)==PCM_BAD_CONFIGURATION);
    init(&f,&pcm,&root,&spark);bind(&f,&pcm);pcm.spark.command_latched=0x1234;
    CHECK(pcm_spark_build(&pcm,&built)==PCM_OK && !built && pcm.spark.command_latched==0x1234);
    init(&f,&pcm,&root,&spark);bind(&f,&pcm);pcm.runtime.spark_running=true;
    f.read_count=2;f.periods[0]=f.periods[1]=2000;f.fail_at=3;pcm.spark.command_latched=0x1234;
    CHECK(pcm_spark_build(&pcm,&built)==PCM_NO_HARDWARE && !built);
    CHECK(pcm.spark.period==2000 && pcm.spark.previous_period==2000 && pcm.spark.command_latched==0x1234);
    init(&f,&pcm,&root,&spark);bind(&f,&pcm);pcm.runtime.spark_running=true;
    f.read_count=2;f.periods[0]=f.periods[1]=2000;
    CHECK(pcm_spark_build(&pcm,&built)==PCM_OK && built);
    init(&f,&pcm,&root,&spark);bind(&f,&pcm);pcm.runtime.spark_running=true;pcm.scheduler.profiling_enabled=true;
    f.platform.task[PCM_SPARK_EXTENSION]=NULL;
    CHECK(pcm_spark_build(&pcm,&built)==PCM_UNIMPLEMENTED && !built && pcm.unresolved_task==PCM_SPARK_EXTENSION);
    init(&f,&pcm,&root,&spark);bind(&f,&pcm);pcm.spark.missing_reference_count=23;
    CHECK(pcm_spark_build(&pcm,&built)==PCM_TRAP_BOUNDARY && !built);
    uint16_t intermediate=0;uint16_t value=pcm_lag16(0,65535,255,&intermediate);
    CHECK(value==pcm_lag16(0,65535,255,NULL) && intermediate==255 && value==256);
    puts("Period/filter calibration, prefix retention, zero seeding, rounding and build-route contracts pass.");
}
static void output_contracts(void)
{
    static Fixture f;Pcm pcm;PcmCalibration root;PcmSparkCalibration spark;
    uint8_t magnitude=91,low,rounded;uint16_t saved=0xbeef;bool published=true;
    init(&f,&pcm,&root,&spark);CHECK(pcm_spark_output_extension(&pcm,NULL)==PCM_BAD_CONFIGURATION);
    pcm.calibration=NULL;CHECK(pcm_spark_output_extension(&pcm,&magnitude)==PCM_OK && magnitude==91);
    pcm.scheduler.profiling_enabled=true;
    CHECK(pcm_spark_output_extension(&pcm,&magnitude)==PCM_UNIMPLEMENTED && magnitude==91);
    CHECK(pcm.unresolved_task==PCM_SPARK_OUTPUT_EXTENSION);
    init(&f,&pcm,&root,&spark);CHECK(pcm_spark_convert(&pcm,NULL)==PCM_BAD_CONFIGURATION);
    pcm.calibration=NULL;CHECK(pcm_spark_convert(&pcm,&saved)==PCM_BAD_CONFIGURATION && saved==0xbeef);
    init(&f,&pcm,&root,&spark);pcm.spark.command=0x1234;pcm.spark.startup_recovery_gain=0xff80;pcm.spark.period_basis=256;
    CHECK(pcm_spark_convert(&pcm,&saved)==PCM_OK && saved==0xffff && !pcm.spark.command_negative);
    init(&f,&pcm,&root,&spark);pcm.spark.command=0x8000;spark.output_latency.values=NULL;
    saved=0xbeef;pcm.spark.output_latency=77;
    CHECK(pcm_spark_convert(&pcm,&saved)==PCM_BAD_CONFIGURATION && saved==0xbeef);
    CHECK(pcm.spark.command_negative && pcm.spark.output_latency==77);
    init(&f,&pcm,&root,&spark);pcm.spark.period=0x1234;pcm.spark.rpm_raw=0x5678;
    pcm.calibration=NULL;pcm.spark.output_request=pcm.reference.consumed=true;
    CHECK(pcm_spark_alternate(&pcm)==PCM_OK && pcm.spark.period_basis==0xffff);
    CHECK(!pcm.spark.output_request && !pcm.reference.consumed && pcm.spark.period==0x1234 && pcm.spark.rpm_raw==0x5678);
    pcm.spark.first_reference=true;CHECK(pcm_spark_alternate(&pcm)==PCM_BAD_CONFIGURATION);
    init(&f,&pcm,&root,&spark);pcm.spark.first_reference=true;pcm.spark.period_basis=88;
    CHECK(pcm_spark_alternate(&pcm)==PCM_NO_HARDWARE && pcm.spark.period_basis==88);
    CHECK(pcm_spark_coordinates(2000,&low,&rounded)==pcm_spark_coordinates(2000,NULL,NULL));
    CHECK(low==7 && rounded==20);
    for (unsigned failure=1;failure<=8;++failure) {
        init(&f,&pcm,&root,&spark);bind(&f,&pcm);f.fail_at=failure;
        CHECK(pcm_spark_handoff(&pcm,0x1234)==PCM_NO_HARDWARE && f.used==failure-1u);
    }
    init(&f,&pcm,&root,&spark);bind(&f,&pcm);pcm.calibration=NULL;f.action=7;pcm.spark.period_correction=0x66;
    CHECK(pcm_spark_handoff(&pcm,0x1234)==PCM_OK && f.used==8);
    CHECK(pcm.spark.period_correction==0x1234 && word(f.memory,0x3fdc)==0x66);
    init(&f,&pcm,&root,&spark);CHECK(pcm_spark_publish(&pcm,NULL)==PCM_BAD_CONFIGURATION);
    bind(&f,&pcm);f.real_alternate=true;
    CHECK(pcm_spark_publish(&pcm,&published)==PCM_OK && !published && f.used==1);
    init(&f,&pcm,&root,&spark);bind(&f,&pcm);f.real_alternate=true;pcm.runtime.spark_running=true;
    CHECK(pcm_spark_publish(&pcm,&published)==PCM_OK && published);
    init(&f,&pcm,&root,&spark);bind(&f,&pcm);pcm.scheduler.profiling_enabled=true;f.action=6;magnitude=91;
    CHECK(pcm_spark_output_extension(&pcm,&magnitude)==PCM_OK && magnitude==(91^0xa5));
    CHECK(pcm.spark.command_negative && pcm.reference.rpm_coordinate==0xc1 && pcm.spark.period_basis==0xff80);
    puts("Output calibration, extension payload, alternate retention, eight failure positions and pre-write latching contracts pass.");
}
static const uint16_t outputs[]={0x06,0x19,0x3d,0x41,0x50,0x61,0x62,0x6e,0x6f,0xa4,0x15a,
    0x1b2,0x1c0,0x1c1,0x1c2,0x1c9,0x1cc,0x1f4,0x1f5,0x1f8,0x1f9,0x1fa,0x1fb,0x1fc,
    0x1fd,0x1fe,0x20a,0x20b,0x22f,0x278,0x2cb,0x83c,0x841,0x843,0x844};
static const uint16_t modifier_outputs[]={0x06,0x19,0x3d,0x41,0x50,0x61,0x62,0x6e,0x6f,0xa4,0x15a,
    0x1b2,0x1c0,0x1c1,0x1c2,0x1c9,0x1cc,0x1f4,0x1f5,0x1f8,0x1f9,0x1fa,0x1fb,0x1fc,
    0x1fd,0x1fe,0x20a,0x20b,0x22f,0x278,0x2cb,0x83c,0x841,0x843,0x844,
    0x63,0x64,0x6c,0xfd,0xfe,0x46,0x51,0x53,0x1d9,0x1f2,0x1f3,0x208,0x837,0x838,0x839,0x83a,0x83b,0x857,0x284};
static const uint16_t command_outputs[]={0x06,0x19,0x3d,0x41,0x50,0x61,0x62,0x6e,0x6f,0xa4,0x15a,
    0x1b2,0x1c0,0x1c1,0x1c2,0x1c9,0x1cc,0x1f4,0x1f5,0x1f8,0x1f9,0x1fa,0x1fb,0x1fc,
    0x1fd,0x1fe,0x20a,0x20b,0x22f,0x278,0x2cb,0x83c,0x841,0x843,0x844,
    0x63,0x64,0x6c,0xfd,0xfe,0x46,0x51,0x53,0x1d9,0x1f2,0x1f3,0x208,0x837,0x838,0x839,0x83a,0x83b,0x857,0x284,
    0x86,0x36,0x3b,0x395,0x398,0x1ee,0x1ef,0x1f0,0x1f1,0x16,0x1da,0x20c,0x20d,0x20e,0x842};
static const uint16_t period_extra[]={0x02,0x04,0x18,0x44,0x4f,0x5f,0x60,0x67,0x68,0x69,0xa7,
    0x1c6,0x1ce,0x1cf,0x1e6,0x1e7,0x1e8,0x1e9,0x1ea,0x1eb,0x1ec,0x1ed,
    0x202,0x210,0x211,0x229,0x257,0x258,0x260,0x261,0x28c,0x28d,0x28e,0x28f,
    0x2ce,0x2f4,0x82e,0x83d,0x83e,0x83f,0x840,0x3060,0x306f,0x880,0x881};
static const uint16_t output_extra[]={0x4b,0x201,0x3fdc,0x3fdd,0x3fe6,0x3fe7,0x3fe8,0x3fe9,0x3ff6,0x3ff7};
static PcmStatus run(Fixture *f,Pcm *pcm,unsigned mode,uint16_t *value)
{
    switch (mode) {
    case 0:return pcm_spark_base(pcm);
    case 1:return pcm_spark_coolant(pcm);
    case 2:return pcm_spark_altitude(pcm);
    case 3:return pcm_spark_egr(pcm);
    case 4:return pcm_spark_sum(pcm);
    case 5:return pcm_spark_mat_effect(pcm);
    case 6:return pcm_spark_mat(pcm);
    case 7:return pcm_spark_pe(pcm);
    case 8:return pcm_spark_auxiliary(pcm);
    case 9:return pcm_spark_terms(pcm);
    case 10: {
        PcmTable2D table={f->memory[0x6000],f->memory[0x6001],f->memory[0x6002],word(f->memory,0x5ffe),f->memory+0x6003};
        uint8_t result=222;PcmStatus status=pcm_lookup2d(f->memory[0x900],f->memory[0x901],&table,&result);
        *value=result;return status;
    }
    case 11:*value=pcm_lag8(f->memory[0x900],word(f->memory,0x902),f->memory[0x904]);return PCM_OK;
    case 12: {
        PcmStatus status=pcm_spark_auxiliary(pcm);
        return status==PCM_OK?pcm_spark_terms(pcm):status;
    }
    case 13: {
        PcmCappedCurve curve={f->memory[0x6300],f->memory[0x905],f->memory+0x6301};uint8_t result=222;
        PcmStatus status=pcm_lookup_capped(f->memory[0x900],&curve,&result);*value=result;return status;
    }
    case 14:return pcm_spark_idle(pcm);
    case 15:return pcm_spark_transient(pcm);
    case 16:return pcm_spark_decel(pcm);
    case 17:return pcm_spark_modifiers(pcm);
    case 18:return pcm_spark_composite(pcm);
    case 19: {
        PcmStatus status=pcm_spark_auxiliary(pcm);
        return status==PCM_OK?pcm_spark_composite(pcm):status;
    }
    case 20:return pcm_spark_extension(pcm);
    case 21:return pcm_spark_override(pcm);
    case 22:return pcm_spark_upper_limit(pcm);
    case 23:return pcm_spark_lower_limit(pcm);
    case 24:return pcm_spark_service(pcm);
    case 25:return pcm_spark_command(pcm);
    case 26:return pcm_spark_calculate(pcm);
    case 27: {
        PcmStatus status=pcm_spark_auxiliary(pcm);
        return status==PCM_OK?pcm_spark_calculate(pcm):status;
    }
    case 28:case 29: {
        *value=pcm_lag16(word(f->memory,0x900),word(f->memory,0x902),f->memory[0x904],&f->partial);
        if (mode==29) { f->memory[0x880]=(uint8_t)(f->partial>>8);f->memory[0x881]=(uint8_t)f->partial; }
        return PCM_OK;
    }
    case 30:*value=pcm_spark_reference_term(word(f->memory,0x900));return PCM_OK;
    case 31:return pcm_spark_period_sample(pcm);
    case 32:return pcm_spark_rpm_filters(pcm);
    case 33:return pcm_spark_period_terms(pcm);
    case 34:return pcm_spark_precompute(pcm);
    case 35:case 37: {
        PcmStatus status=mode==37?pcm_spark_auxiliary(pcm):PCM_OK;
        if (status!=PCM_OK) return status;
        bool built;status=pcm_spark_build(pcm,&built);*value=built;return status;
    }
    case 36: {
        PcmStatus status=pcm_spark_precompute(pcm);
        return status==PCM_OK?pcm_spark_calculate(pcm):status;
    }
    case 38:*value=pcm_spark_coordinates(word(f->memory,0x900),&f->coordinate_low,&f->coordinate_rounded);return PCM_OK;
    case 39: {
        uint8_t magnitude=f->memory[0x900];PcmStatus status=pcm_spark_output_extension(pcm,&magnitude);
        *value=magnitude;return status;
    }
    case 40:*value=0xbeef;return pcm_spark_convert(pcm,value);
    case 41:return pcm_spark_handoff(pcm,word(f->memory,0x900));
    case 42:return pcm_spark_output(pcm);
    case 43:return pcm_spark_alternate(pcm);
    case 44:case 46: {
        PcmStatus status=mode==46?pcm_spark_auxiliary(pcm):PCM_OK;
        if (status!=PCM_OK) return status;
        bool published;status=pcm_spark_publish(pcm,&published);*value=published;return status;
    }
    case 45: {
        bool built;PcmStatus status=pcm_spark_build(pcm,&built);*value=built;return status;
    }
    default:return PCM_BAD_CONFIGURATION;
    }
}
int main(int argc,char **argv)
{
    static Fixture f;Pcm pcm;PcmCalibration root;PcmSparkCalibration spark;
    if (argc==2 && strcmp(argv[1],"--contracts")==0) { contracts();return 0; }
    if (argc==2 && strcmp(argv[1],"--modifier-contracts")==0) { modifier_contracts();return 0; }
    if (argc==2 && strcmp(argv[1],"--command-contracts")==0) { command_contracts();return 0; }
    if (argc==2 && strcmp(argv[1],"--period-contracts")==0) { period_contracts();return 0; }
    if (argc==2 && strcmp(argv[1],"--output-contracts")==0) { output_contracts();return 0; }
    if (argc==2 && strcmp(argv[1],"--defaults")==0) {
        init(&f,&pcm,&root,&spark);printf("[");bool first=true;
        for (unsigned a=0;a<65536;++a) if (f.present[a]) { printf("%s[%u,%u]",first?"":",",a,f.memory[a]);first=false; }
        puts("]");return 0;
    }
    unsigned mode,count;
    while (scanf("%u %u",&mode,&count)==2) {
        if (mode>46 || count>2048) return 2;
        init(&f,&pcm,&root,&spark);
        for (unsigned i=0;i<count;++i) {
            unsigned a,v;if (scanf("%u %u",&a,&v)!=2 || a>65535 || v>255) return 2;f.memory[a]=(uint8_t)v;
        }
        transfer(&pcm,f.memory,state_map,sizeof(state_map)/sizeof(state_map[0]),true);load_cal(&f,&root,&spark);
        if (mode>=20) {
            bind(&f,&pcm);f.fail_at=f.memory[0x907];f.action=f.memory[0x908];f.masked=f.memory[0x909]!=0;
            if (f.memory[0x90a]) f.platform.task[PCM_SPARK_EXTENSION]=NULL;
            if (mode>=28) {
                if (f.memory[0x90c]) f.platform.task[PCM_ALTERNATE_RPM]=NULL;
                f.read_count=f.memory[0x90b];CHECK(f.read_count<=16);
                for (unsigned i=0;i<f.read_count;++i) f.periods[i]=word(f.memory,(uint16_t)(0x910+i*2u));
            }
            if (mode>=38) {
                f.real_alternate=true;
                if (f.memory[0x90d]) f.platform.task[PCM_SPARK_OUTPUT_EXTENSION]=NULL;
            }
        }
        uint16_t value=0;PcmStatus status=run(&f,&pcm,mode,&value);
        transfer(&pcm,f.memory,state_map,sizeof(state_map)/sizeof(state_map[0]),false);
        CHECK(pcm.unresolved_task==PCM_TASK_COUNT || (mode>=20 && pcm.unresolved_task==PCM_SPARK_EXTENSION) ||
              (mode>=28 && pcm.unresolved_task==PCM_ALTERNATE_RPM) ||
              (mode>=38 && pcm.unresolved_task==PCM_SPARK_OUTPUT_EXTENSION));
        CHECK(mode>=20 || pcm.platform==NULL);
        printf("{\"status\":%u,\"value\":%u,\"state\":[",(unsigned)status,(unsigned)value);
        const uint16_t *selected=mode>=20?command_outputs:mode>=13?modifier_outputs:outputs;
        size_t size=mode>=20?sizeof(command_outputs)/sizeof(command_outputs[0]):mode>=13?sizeof(modifier_outputs)/sizeof(modifier_outputs[0]):sizeof(outputs)/sizeof(outputs[0]);
        for (size_t i=0;i<size;++i) printf("%s%u",i?",":"",f.memory[selected[i]]);
        if (mode>=28) for (size_t i=0;i<sizeof(period_extra)/sizeof(period_extra[0]);++i) printf(",%u",f.memory[period_extra[i]]);
        if (mode>=38) for (size_t i=0;i<sizeof(output_extra)/sizeof(output_extra[0]);++i) printf(",%u",f.memory[output_extra[i]]);
        if (mode<20) puts("]}");
        else {
            unsigned unresolved=pcm.unresolved_task==PCM_SPARK_EXTENSION?1u:pcm.unresolved_task==PCM_ALTERNATE_RPM?2u:
                                pcm.unresolved_task==PCM_SPARK_OUTPUT_EXTENSION?3u:0u;
            printf("],\"masked\":%u,\"unresolved\":%u",(unsigned)f.masked,unresolved);
            if (mode>=28) printf(",\"partial\":%u",(unsigned)f.partial);
            if (mode>=38) printf(",\"coordinates\":[%u,%u]",(unsigned)f.coordinate_low,(unsigned)f.coordinate_rounded);
            printf(",\"events\":[");
            for (unsigned i=0;i<f.used;++i) { Event *e=&f.events[i];printf("%s[\"%c\",%u,%u,%u,%u]",i?",":"",e->kind,e->width,e->address,e->value,(unsigned)e->masked); }
            puts("]}");
        }
    }
    return 0;
}
