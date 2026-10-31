#include "spark.h"
#include "hardware.h"
#include "calibration.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CHECK(x) do { if (!(x)) { fprintf(stderr,"Admission check %d: %s\n",__LINE__,#x);exit(1); } } while (0)
typedef struct { uint16_t address;uint8_t mask,width;size_t offset; } Mapping;
#define B(a,m) {a,0,8,offsetof(Pcm,m)}
#define W(a,m) {a,0,16,offsetof(Pcm,m)}
#define F(a,b,m) {a,b,0,offsetof(Pcm,m)}
static const Mapping state_map[]={
    B(0x1c6,spark.map_filtered),B(0x2f4,spark.barometric_high),B(0x1ce,spark.normalized_load_divisor),
    W(0x257,spark.density),B(0x1c9,spark.vacuum),B(0x1c0,spark.load_coordinate),B(0x1cf,spark.normalized_load),
    B(0x6f,spark.load_status),B(0x229,spark.map_fault_count),F(0x18,0x10,spark.map_fault),
    B(0x82e,reference.map_sample),B(0x61,spark.rpm_low_coordinate),B(0x1d9,reference.throttle),
    F(0x50,0x20,reference.pending),F(0x50,0x04,reference.consumed),
    F(0x4f,0x10,runtime.fuel_running),F(0x4f,0x80,runtime.spark_running),F(0x4f,0x40,spark.startup_gain_enabled),
    F(0x44,0x08,spark.first_reference),F(0x51,0x40,spark.startup_gain_complete),F(0x04,0x08,spark.run_transition),
    B(0x211,spark.fuel_run_count),B(0x210,spark.spark_run_count),B(0x202,spark.missing_reference_count),
    W(0x260,spark.reference_age),W(0x1ea,spark.adaptive_period),W(0x5f,spark.period_basis),
    W(0x1f2,spark.startup_recovery_gain),B(0x2ce,reference.event_age)
};
#undef B
#undef W
#undef F
#define B(a,m) {a,0,8,offsetof(PcmSparkCalibration,m)}
#define W(a,m) {a,0,16,offsetof(PcmSparkCalibration,m)}
static const Mapping cal_map[]={
    W(0x4133,spark_run_period_limit),W(0x4135,fuel_run_period_limit),W(0x4962,no_reference_age_limit),
    B(0x4142,spark_run_events),B(0x4143,fuel_run_events),B(0x414e,startup_gain),
    B(0x4e64,map_sample_minimum),B(0x4e65,map_rpm_minimum),B(0x4e66,map_count_limit),
    B(0x4e67,map_throttle_limit),B(0x4d96,missing_reference_age_cap)
};
#undef B
#undef W
typedef struct { char kind;uint8_t width;uint16_t address,value;bool masked; } Event;
typedef struct {
    uint8_t memory[65536];Event events[16];unsigned used,attempts,fail_at,action,read_count,read_index;
    uint16_t periods[4];bool masked;Pcm *pcm;PcmPlatform platform;
} Fixture;
static uint16_t word(const uint8_t *m,unsigned a)
{ return (uint16_t)((uint16_t)m[a]*256u+m[a+1u]); }
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
        } else {
            volatile uint8_t *value=field;
            if (load) *value=memory[m->address];else memory[m->address]=*value;
        }
    }
}
static PcmStatus record(Fixture *f,char kind,uint8_t width,uint16_t address,uint16_t value)
{
    if (++f->attempts==f->fail_at) return PCM_NO_HARDWARE;
    CHECK(f->used<16);f->events[f->used++]=(Event){kind,width,address,value,f->masked};return PCM_OK;
}
static PcmStatus read8(void *context,uint16_t address,uint8_t *value)
{
    Fixture *f=context;CHECK(address==PCM_BOARD_3060);
    uint8_t sample=f->memory[address];PcmStatus status=record(f,'R',8,address,sample);
    if (status==PCM_OK) *value=sample;
    return status;
}
static PcmStatus read16(void *context,uint16_t address,uint16_t *value)
{
    Fixture *f=context;CHECK(address==PCM_REFERENCE_PERIOD);
    uint16_t sample=word(f->memory,address);
    if (f->read_count) { CHECK(f->read_index<f->read_count);sample=f->periods[f->read_index++]; }
    PcmStatus status=record(f,'R',16,address,sample);
    if (status==PCM_OK) {
        *value=sample;
        if (f->action==1) {
            f->pcm->spark.startup_gain_enabled=true;f->pcm->spark.startup_gain_complete=false;
            f->pcm->spark.startup_recovery_gain=0x8000;
        }
    }
    return status;
}
static PcmStatus write8(void *context,uint16_t address,uint8_t value)
{
    Fixture *f=context;CHECK(address==PCM_BOARD_3060 || address==PCM_REFERENCE_AGE);
    PcmStatus status=record(f,'W',8,address,value);
    if (status==PCM_OK) f->memory[address]=value;
    return status;
}
static PcmStatus mask(void *context,bool masked)
{
    Fixture *f=context;PcmStatus status=record(f,'M',0,0,masked);
    if (status==PCM_OK) {
        f->masked=masked;
        if (!masked && f->action==2) { f->pcm->reference.pending=true;f->pcm->runtime.spark_running=true; }
    }
    return status;
}
static PcmStatus alternate(Pcm *pcm,PcmTask task)
{
    CHECK(task==PCM_ALTERNATE_RPM);Fixture *f=pcm->platform->context;
    PcmStatus status=record(f,'T',0,0xac51,(uint16_t)f->action);
    if (status==PCM_OK && f->action==3) {
        pcm->reference.consumed=false;pcm->spark.period_basis=0xffff;pcm->spark.rpm_low_coordinate=0x77;
    }
    return status;
}
static void init(Fixture *f,Pcm *pcm,PcmCalibration *root,PcmSparkCalibration *cal)
{
    memset(f,0,sizeof(*f));memset(pcm,0,sizeof(*pcm));
    *root=pcm_reference_scheduler_calibration;*cal=pcm_reference_spark_calibration;
    root->spark=cal;pcm->calibration=root;pcm->unresolved_task=PCM_TASK_COUNT;f->pcm=pcm;
    f->platform.context=f;f->platform.read8=read8;f->platform.read16=read16;
    f->platform.write8=write8;f->platform.mask_irq=mask;f->platform.task[PCM_ALTERNATE_RPM]=alternate;
    pcm->platform=&f->platform;
    transfer(cal,f->memory,cal_map,sizeof(cal_map)/sizeof(cal_map[0]),false);
}
static void contracts(void)
{
    static Fixture f;Pcm pcm;PcmCalibration root;PcmSparkCalibration cal;bool normal=true;
    init(&f,&pcm,&root,&cal);CHECK(pcm_spark_admit(&pcm,NULL)==PCM_BAD_CONFIGURATION);
    CHECK(pcm_spark_prepare(&pcm,NULL)==PCM_BAD_CONFIGURATION && f.used==0);
    const PcmRoutine routines[]={pcm_spark_map_check,pcm_spark_fuel_admit};
    for (unsigned i=0;i<2;++i) {
        init(&f,&pcm,&root,&cal);pcm.calibration=NULL;CHECK(routines[i](&pcm)==PCM_BAD_CONFIGURATION && f.used==0);
        init(&f,&pcm,&root,&cal);root.spark=NULL;CHECK(routines[i](&pcm)==PCM_BAD_CONFIGURATION && f.used==0);
    }
    init(&f,&pcm,&root,&cal);pcm.calibration=NULL;
    CHECK(pcm_spark_admit(&pcm,&normal)==PCM_BAD_CONFIGURATION && !normal && f.used==0);
    CHECK(pcm_spark_load(&pcm)==PCM_OK && f.used==0);
    init(&f,&pcm,&root,&cal);pcm.platform=NULL;
    CHECK(pcm_spark_timeout(&pcm)==PCM_NO_HARDWARE && pcm.spark.period_basis==0xffff);
    init(&f,&pcm,&root,&cal);f.platform.read16=NULL;pcm.reference.pending=true;pcm.runtime.spark_running=true;
    pcm.spark.adaptive_period=100;pcm.spark.missing_reference_count=22;
    CHECK(pcm_spark_admit(&pcm,&normal)==PCM_NO_HARDWARE && !normal);
    CHECK(!pcm.reference.pending && pcm.reference.consumed && pcm.spark.adaptive_period==87 && pcm.spark.missing_reference_count==0);
    init(&f,&pcm,&root,&cal);f.platform.task[PCM_ALTERNATE_RPM]=NULL;pcm.reference.pending=true;
    CHECK(pcm_spark_admit(&pcm,&normal)==PCM_UNIMPLEMENTED && !normal && pcm.spark.first_reference);
    CHECK(pcm.unresolved_task==PCM_ALTERNATE_RPM);
    init(&f,&pcm,&root,&cal);pcm.calibration=NULL;
    CHECK(pcm_spark_timeout(&pcm)==PCM_TRAP_BOUNDARY && f.used==2);
    init(&f,&pcm,&root,&cal);pcm.runtime.spark_running=true;f.platform.mask_irq=NULL;
    CHECK(pcm_spark_admit(&pcm,&normal)==PCM_NO_HARDWARE && pcm.spark.reference_age==1 && !normal);
    init(&f,&pcm,&root,&cal);root.spark=NULL;pcm.spark.barometric_high=200;pcm.spark.map_filtered=100;
    CHECK(pcm_spark_prepare(&pcm,&normal)==PCM_BAD_CONFIGURATION && pcm.spark.load_coordinate!=0 && !normal);
    puts("Admission configuration, independent run gates, missing-I/O/dependency and trap contracts pass.");
}
static const uint16_t outputs[]={0x04,0x18,0x44,0x4f,0x50,0x51,0x5f,0x60,0x61,0x6f,
    0x1c0,0x1c6,0x1c9,0x1ce,0x1cf,0x1d9,0x1ea,0x1eb,0x1f2,0x1f3,0x202,0x210,0x211,
    0x229,0x257,0x258,0x260,0x261,0x2ce,0x2f4,0x82e,0x3060,0x306f};
int main(int argc,char **argv)
{
    static Fixture f;Pcm pcm;PcmCalibration root;PcmSparkCalibration cal;
    if (argc==2 && strcmp(argv[1],"--contracts")==0) { contracts();return 0; }
    if (argc==2 && strcmp(argv[1],"--defaults")==0) {
        init(&f,&pcm,&root,&cal);printf("[");bool first=true;
        for (size_t i=0;i<sizeof(cal_map)/sizeof(cal_map[0]);++i)
            for (unsigned j=0;j<cal_map[i].width/8u;++j) {
                unsigned a=cal_map[i].address+j;printf("%s[%u,%u]",first?"":",",a,f.memory[a]);first=false;
            }
        puts("]");return 0;
    }
    unsigned mode,fail,masked,missing,action,reads,count;
    while (scanf("%u %u %u %u %u %u %u",&mode,&fail,&masked,&missing,&action,&reads,&count)==7) {
        if (mode>5 || reads>4 || count>256) return 2;
        init(&f,&pcm,&root,&cal);f.fail_at=fail;f.masked=masked!=0;f.action=action;f.read_count=reads;
        for (unsigned i=0;i<reads;++i) { unsigned value;if (scanf("%u",&value)!=1 || value>65535) return 2;f.periods[i]=(uint16_t)value; }
        for (unsigned i=0;i<count;++i) {
            unsigned a,v;if (scanf("%u %u",&a,&v)!=2 || a>65535 || v>255) return 2;f.memory[a]=(uint8_t)v;
        }
        transfer(&pcm,f.memory,state_map,sizeof(state_map)/sizeof(state_map[0]),true);
        transfer(&cal,f.memory,cal_map,sizeof(cal_map)/sizeof(cal_map[0]),true);
        if (missing) f.platform.task[PCM_ALTERNATE_RPM]=NULL;
        bool normal=false;PcmStatus status;
        switch (mode) {
        case 0:status=pcm_spark_load(&pcm);break;
        case 1:status=pcm_spark_map_check(&pcm);break;
        case 2:status=pcm_spark_fuel_admit(&pcm);break;
        case 3:status=pcm_spark_timeout(&pcm);break;
        case 4:status=pcm_spark_admit(&pcm,&normal);break;
        default:status=pcm_spark_prepare(&pcm,&normal);break;
        }
        transfer(&pcm,f.memory,state_map,sizeof(state_map)/sizeof(state_map[0]),false);
        CHECK(pcm.unresolved_task==PCM_TASK_COUNT || pcm.unresolved_task==PCM_ALTERNATE_RPM);
        printf("{\"status\":%u,\"normal\":%u,\"masked\":%u,\"unresolved\":%u,\"state\":[",(unsigned)status,(unsigned)normal,(unsigned)f.masked,(unsigned)(pcm.unresolved_task==PCM_ALTERNATE_RPM));
        for (size_t i=0;i<sizeof(outputs)/sizeof(outputs[0]);++i) printf("%s%u",i?",":"",f.memory[outputs[i]]);
        printf("],\"events\":[");
        for (unsigned i=0;i<f.used;++i) {
            const Event *e=&f.events[i];printf("%s[\"%c\",%u,%u,%u,%u]",i?",":"",e->kind,e->width,e->address,e->value,(unsigned)e->masked);
        }
        puts("]}");
    }
    return 0;
}
