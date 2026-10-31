#include "spark.h"
#include "reference_math.h"
#include "calibration.h"
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
    B(0x83c,spark.mat_effect),B(0x841,knock.octane_rpm_factor),B(0x843,knock.event_gain),B(0x844,knock.retard_limit)
};
#undef B
#undef W
#undef F
#define B(a,m) {a,8,0,1,offsetof(PcmCalibration,m)}
#define A(a,n,m) {a,8,0,n,offsetof(PcmCalibration,m)}
static const Mapping root_map[]={
    B(0x400b,reference.mode_b),B(0x400d,mode_d),B(0x45da,knock.minimum_coolant),
    A(0x4585,8,knock.pe_retard_cap),A(0x458d,7,knock.cruise_retard_cap),
    A(0x4594,17,knock.event_gain_curve),A(0x45be,9,knock.octane_rpm),A(0x45c7,17,knock.octane_load)
};
#undef B
#undef A
#define B(a,m) {a,8,0,1,offsetof(PcmSparkCalibration,m)}
#define A(a,n,m) {a,8,0,n,offsetof(PcmSparkCalibration,m)}
static const Mapping spark_map[]={
    B(0x43ae,coolant_mode),B(0x4439,mat_mode),B(0x485f,egr_mode),B(0x485e,egr_gain),
    B(0x413b,base_bias),B(0x413c,coolant_bias),B(0x413d,altitude_bias),B(0x413e,egr_bias),
    B(0x413f,mat_bias),B(0x4140,idle_coolant_threshold),B(0x55f2,transmission_bias),
    A(0x449d,17,mat_negative_gain),A(0x44ae,17,mat_positive_gain),A(0x44bf,17,pe_curve)
};
#undef B
#undef A
typedef struct { uint16_t address,capacity;size_t offset; } TableMapping;
#define T(a,n,m) {a,n,offsetof(PcmSparkCalibration,m)}
static const TableMapping tables[]={T(0x4166,289,base_normal),T(0x428a,289,base_idle),
    T(0x43af,144,coolant),T(0x44d5,66,altitude),T(0x443a,109,mat),T(0x4860,79,egr)};
#undef T
typedef struct { uint8_t memory[65536],present[65536],data[6][527]; } Fixture;
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
        for (size_t i=0;i<count;++i) for (unsigned j=0;j<map[i].count;++j) put(f,map[i].address+j,object[map[i].offset+j]);
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
static const uint16_t outputs[]={0x06,0x19,0x3d,0x41,0x50,0x61,0x62,0x6e,0x6f,0xa4,0x15a,
    0x1b2,0x1c0,0x1c1,0x1c2,0x1c9,0x1cc,0x1f4,0x1f5,0x1f8,0x1f9,0x1fa,0x1fb,0x1fc,
    0x1fd,0x1fe,0x20a,0x20b,0x22f,0x278,0x2cb,0x83c,0x841,0x843,0x844};
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
    default:return PCM_BAD_CONFIGURATION;
    }
}
int main(int argc,char **argv)
{
    static Fixture f;Pcm pcm;PcmCalibration root;PcmSparkCalibration spark;
    if (argc==2 && strcmp(argv[1],"--contracts")==0) { contracts();return 0; }
    if (argc==2 && strcmp(argv[1],"--defaults")==0) {
        init(&f,&pcm,&root,&spark);printf("[");bool first=true;
        for (unsigned a=0;a<65536;++a) if (f.present[a]) { printf("%s[%u,%u]",first?"":",",a,f.memory[a]);first=false; }
        puts("]");return 0;
    }
    unsigned mode,count;
    while (scanf("%u %u",&mode,&count)==2) {
        if (mode>12 || count>2048) return 2;
        init(&f,&pcm,&root,&spark);
        for (unsigned i=0;i<count;++i) {
            unsigned a,v;if (scanf("%u %u",&a,&v)!=2 || a>65535 || v>255) return 2;f.memory[a]=(uint8_t)v;
        }
        transfer(&pcm,f.memory,state_map,sizeof(state_map)/sizeof(state_map[0]),true);load_cal(&f,&root,&spark);
        uint16_t value=0;PcmStatus status=run(&f,&pcm,mode,&value);
        transfer(&pcm,f.memory,state_map,sizeof(state_map)/sizeof(state_map[0]),false);
        CHECK(pcm.unresolved_task==PCM_TASK_COUNT && pcm.platform==NULL);
        printf("{\"status\":%u,\"value\":%u,\"state\":[",(unsigned)status,(unsigned)value);
        for (size_t i=0;i<sizeof(outputs)/sizeof(outputs[0]);++i) printf("%s%u",i?",":"",f.memory[outputs[i]]);
        puts("]}");
    }
    return 0;
}
