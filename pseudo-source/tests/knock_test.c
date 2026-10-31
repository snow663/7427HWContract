#include "knock.h"
#include "hardware.h"
#include "scheduler.h"
#include "calibration.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CHECK(x) do { if (!(x)) { fprintf(stderr,"Knock contract failed at %d: %s\n",__LINE__,#x);exit(1); } } while (0)
typedef struct { uint16_t address; uint8_t width, mask, count; size_t offset; } Mapping;
#define B(a,m) {a,8,0,1,offsetof(Pcm,m)}
#define W(a,m) {a,16,0,1,offsetof(Pcm,m)}
#define F(a,b,m) {a,0,b,1,offsetof(Pcm,m)}
static const Mapping state_map[] = {
    B(0x02,scheduler.phase), B(0x06,reference.coolant), B(0x16,runtime.primary_faults),
    F(0x19,0x10,knock.sensor_fault), F(0x1a,0x02,runtime.adc_timeout), F(0x3a,0x01,runtime.adc_fault),
    B(0x62,reference.rpm_coordinate), B(0x63,spark.rpm_high), F(0x6e,0x02,knock.burst_active),
    W(0x1ee,spark.command), W(0x203,knock.sample_baseline), B(0x207,knock.sensor_fault_count),
    B(0x20c,knock.retard), B(0x20d,knock.observation_accumulator), B(0x284,spark.vehicle_speed_high),
    B(0x843,knock.event_gain), B(0x844,knock.retard_limit)
};
#undef B
#undef W
#undef F
#define B(a,m) {a,8,0,1,offsetof(PcmCalibration,m)}
#define A(a,n,m) {a,8,0,n,offsetof(PcmCalibration,m)}
static const Mapping cal_map[] = {
    A(0x45a5,17,knock.decay_rate), B(0x45d8,knock.minimum_speed), B(0x45d9,knock.minimum_rpm_high),
    B(0x45da,knock.minimum_coolant), B(0x4e74,knock.sensor_fault_delay), B(0x4e75,knock.sensor_upper),
    B(0x4e76,knock.sensor_lower), B(0x4e77,knock.fault_retard), B(0x5b03,reference.diagnostic_options),
    A(0x45db,64,knock.noise_floor), A(0x461c,64,knock.observation_bias)
};
#undef B
#undef A
static uint16_t word(const uint8_t *memory,uint16_t address)
{ return (uint16_t)((uint16_t)memory[address]*256u+memory[(uint16_t)(address+1u)]); }
static void transfer(void *object,uint8_t *memory,const Mapping *mapping,size_t count,bool load)
{
    for (size_t i=0;i<count;++i) {
        const Mapping *m=&mapping[i];uint8_t *field=(uint8_t *)object+m->offset;
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
typedef struct { char kind; unsigned width; uint16_t address,value; bool masked; } Event;
typedef struct {
    uint8_t memory[65536];Event events[128];
    unsigned used,attempts,fail_at,polls,ready_after,port_reads,irq_point;
    int second_port;
    bool masked,injected;
    Pcm *pcm;
    PcmPlatform platform;
} Fixture;
static PcmStatus record(Fixture *f,char kind,unsigned width,uint16_t address,uint16_t value)
{
    if (++f->attempts==f->fail_at) return PCM_NO_HARDWARE;
    CHECK(f->used<128);
    f->events[f->used++]=(Event){kind,width,address,value,f->masked};return PCM_OK;
}
static PcmStatus read8(void *v,uint16_t address,uint8_t *out)
{
    Fixture *f=v;uint8_t value=f->memory[address];
    if (address==PCM_ADCTL && f->ready_after && f->polls+1>=f->ready_after) value|=0x80;
    if (address==PCM_PORTD && f->port_reads==1 && f->second_port>=0) value=(uint8_t)f->second_port;
    PcmStatus status=record(f,'R',8,address,value);
    if (status==PCM_OK) {
        *out=value;if (address==PCM_ADCTL) ++f->polls;if (address==PCM_PORTD) ++f->port_reads;
    }
    return status;
}
static PcmStatus read16(void *v,uint16_t address,uint16_t *out)
{
    Fixture *f=v;uint16_t value=word(f->memory,address);
    PcmStatus status=record(f,'R',16,address,value);if (status==PCM_OK) *out=value;return status;
}
static PcmStatus write8(void *v,uint16_t address,uint8_t value)
{
    Fixture *f=v;PcmStatus status=record(f,'W',8,address,value);
    if (status==PCM_OK) {
        if (address==PCM_TFLG1) f->memory[address]&=(uint8_t)~value;
        else f->memory[address]=value;
        if (address==PCM_ADCTL) f->polls=0;
    }
    return status;
}
static PcmStatus inject(Fixture *f)
{
    f->injected=true;
    if (f->masked) return PCM_OK; /* Modeled maskable request is rejected. */
    f->masked=true;PcmStatus status=pcm_oc1_irq(f->pcm);
    if (status==PCM_OK) f->masked=false;
    return status;
}
static PcmStatus mask(void *v,bool masked)
{
    Fixture *f=v;PcmStatus status;
    if (!f->injected && f->irq_point==1 && masked) {
        status=inject(f);if (status!=PCM_OK) return status;
    }
    status=record(f,'M',0,0,masked);
    if (status!=PCM_OK) return status;
    f->masked=masked;
    if (!f->injected && ((f->irq_point==2 && masked)||(f->irq_point==3 && !masked))) return inject(f);
    return PCM_OK;
}
static void init(Fixture *f,Pcm *pcm,PcmCalibration *cal)
{
    memset(f,0,sizeof(*f));memset(pcm,0,sizeof(*pcm));*cal=pcm_reference_scheduler_calibration;
    f->platform.context=f;f->platform.read8=read8;f->platform.read16=read16;
    f->platform.write8=write8;f->platform.mask_irq=mask;
    f->pcm=pcm;f->second_port=-1;f->ready_after=1;
    pcm->platform=&f->platform;pcm->calibration=cal;pcm->unresolved_task=PCM_TASK_COUNT;
    transfer(cal,f->memory,cal_map,sizeof(cal_map)/sizeof(cal_map[0]),false);
}
static void contracts(void)
{
    static Fixture f;Pcm pcm;PcmCalibration cal;
    const PcmRoutine routines[]={pcm_knock_decay,pcm_knock_sensor,pcm_knock_retard,pcm_slot_08};
    for (unsigned i=0;i<4;++i) {
        init(&f,&pcm,&cal);pcm.calibration=NULL;
        CHECK(routines[i](&pcm)==PCM_BAD_CONFIGURATION && f.used==0);
    }
    init(&f,&pcm,&cal);pcm.platform=NULL;
    CHECK(pcm_knock_decay(&pcm)==PCM_OK);
    cal.reference.diagnostic_options&=(uint8_t)~0x10;
    CHECK(pcm_knock_sensor(&pcm)==PCM_OK);
    CHECK(pcm_slot_08(&pcm)==PCM_OK);
    CHECK(pcm_knock_retard(&pcm)==PCM_NO_HARDWARE);
    init(&f,&pcm,&cal);f.platform.read8=NULL;
    CHECK(pcm_knock_sensor(&pcm)==PCM_NO_HARDWARE && f.used==0);
    init(&f,&pcm,&cal);f.platform.write8=NULL;
    CHECK(pcm_knock_sensor(&pcm)==PCM_NO_HARDWARE && f.used==1);
    init(&f,&pcm,&cal);f.platform.mask_irq=NULL;
    CHECK(pcm_knock_sensor(&pcm)==PCM_NO_HARDWARE && f.used==4);
    init(&f,&pcm,&cal);f.platform.read8=NULL;pcm.runtime.adc_timeout=true;
    CHECK(pcm_adc_convert(&pcm,1)==PCM_NO_HARDWARE && f.used==1 && !pcm.runtime.adc_timeout);
    init(&f,&pcm,&cal);f.platform.write8=NULL;pcm.runtime.adc_timeout=true;
    CHECK(pcm_adc_convert(&pcm,1)==PCM_NO_HARDWARE && f.used==0 && !pcm.runtime.adc_timeout);
    init(&f,&pcm,&cal);pcm.knock.observation_accumulator=73;f.platform.mask_irq=NULL;
    CHECK(pcm_knock_retard(&pcm)==PCM_NO_HARDWARE && pcm.knock.observation_accumulator==73);
    init(&f,&pcm,&cal);pcm.knock.observation_accumulator=73;f.fail_at=2;
    CHECK(pcm_knock_retard(&pcm)==PCM_NO_HARDWARE && pcm.knock.observation_accumulator==0 && f.masked);
    puts("Knock configuration, missing-callback and literal-mask contracts pass.");
}
static PcmStatus run(Fixture *f,Pcm *pcm,unsigned mode,uint8_t argument)
{
    switch (mode) {
    case 0:return pcm_knock_decay(pcm);
    case 1:return pcm_knock_sensor(pcm);
    case 2:return pcm_slot_08(pcm);
    case 3:return pcm_knock_retard(pcm);
    case 4:return pcm_adc_mux(pcm,argument);
    case 5:return pcm_adc_convert(pcm,argument);
    case 6: {
        PcmStatus status=inject(f);
        if (status==PCM_OK) status=pcm_knock_retard(pcm);
        if (status==PCM_OK) status=pcm_slot_08(pcm);
        if (status==PCM_OK) status=pcm_knock_retard(pcm);
        return status;
    }
    default:return PCM_BAD_CONFIGURATION;
    }
}
static const uint16_t outputs[]={0x02,0x06,0x16,0x19,0x1a,0x3a,0x62,0x63,0x6e,0x1ee,0x1ef,
    0x203,0x204,0x207,0x20c,0x20d,0x284,0x843,0x844,0x3008,0x3030,0x3034,0x3023};
int main(int argc,char **argv)
{
    static Fixture f;Pcm pcm;PcmCalibration cal;
    if (argc==2 && strcmp(argv[1],"--contracts")==0) { contracts();return 0; }
    if (argc==2 && strcmp(argv[1],"--defaults")==0) {
        init(&f,&pcm,&cal);printf("[");bool first=true;
        for (size_t i=0;i<sizeof(cal_map)/sizeof(cal_map[0]);++i) for (unsigned j=0;j<cal_map[i].count;++j) {
            unsigned address=cal_map[i].address+j;printf("%s[%u,%u]",first?"":",",address,f.memory[address]);first=false;
        }
        puts("]");return 0;
    }
    unsigned mode,fail,masked,ready,point,argument,count;int second_port;
    while (scanf("%u %u %u %u %d %u %u %u",&mode,&fail,&masked,&ready,&second_port,&point,&argument,&count)==8) {
        if (mode>6 || masked>1 || ready>13 || second_port>255 || second_port< -1 || point>3 || argument>255 || count>512) return 2;
        init(&f,&pcm,&cal);f.fail_at=fail;f.masked=masked!=0;f.ready_after=ready;
        f.second_port=second_port;f.irq_point=point;
        for (unsigned i=0;i<count;++i) {
            unsigned address,value;if (scanf("%u %u",&address,&value)!=2 || address>65535 || value>255) return 2;
            f.memory[address]=(uint8_t)value;
        }
        transfer(&pcm,f.memory,state_map,sizeof(state_map)/sizeof(state_map[0]),true);
        transfer(&cal,f.memory,cal_map,sizeof(cal_map)/sizeof(cal_map[0]),true);
        PcmStatus status=run(&f,&pcm,mode,(uint8_t)argument);
        CHECK(pcm.unresolved_task==PCM_TASK_COUNT);
        transfer(&pcm,f.memory,state_map,sizeof(state_map)/sizeof(state_map[0]),false);
        printf("{\"status\":%u,\"state\":[",(unsigned)status);
        for (size_t i=0;i<sizeof(outputs)/sizeof(outputs[0]);++i) printf("%s%u",i?",":"",f.memory[outputs[i]]);
        printf("],\"masked\":%u,\"events\":[",(unsigned)f.masked);
        for (unsigned i=0;i<f.used;++i) {
            Event *e=&f.events[i];printf("%s[\"%c\",%u,%u,%u,%u]",i?",":"",e->kind,e->width,e->address,e->value,(unsigned)e->masked);
        }
        puts("]}");
    }
    return 0;
}
