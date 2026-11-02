#include "fuel.h"
#include "control.h"
#include "scheduler.h"
#include "fuel_output_fixture_map.h"

#define CHECK(x) do { if (!(x)) { fprintf(stderr,"Fuel fixture check %d: %s\n",__LINE__,#x);exit(1); } } while (0)
typedef struct { char kind; unsigned width; uint16_t address,value; bool masked; } Event;
typedef struct {
    uint8_t memory[65536]; Event events[4096];
    unsigned used,attempts,fail_at,polls,control,action;
    bool masked; Pcm *pcm; PcmPlatform platform;
} Fixture;
static PcmStatus record(Fixture *f,char kind,unsigned width,uint16_t address,uint16_t value)
{
    if (++f->attempts==f->fail_at) return PCM_NO_HARDWARE;
    CHECK(f->used<SIZE(f->events));
    f->events[f->used++]=(Event){kind,width,address,value,f->masked};return PCM_OK;
}
static PcmStatus read8(void *v,uint16_t a,uint8_t *out)
{
    Fixture *f=v;uint8_t sample=f->memory[a];
    if (f->memory[0x90a]) {
        unsigned mux=(f->memory[PCM_PORTD]>>3)&7u;
        if (a==PCM_ADR4 && (mux==7 || mux==6 || mux==1)) sample=f->memory[mux==7?0x90b:mux==6?0x90c:0x90d];
        if (f->control==0x11 && a==PCM_ADR2) sample=f->memory[0x90e];
        if (f->control==0x11 && a==PCM_ADR3) sample=f->memory[0x90f];
    }
    if (a==PCM_ADCTL) {
        unsigned limit=f->memory[f->control==7?0x900:f->control==0x14?0x901:0x902];
        sample=(uint8_t)((sample&0x7f)|(f->polls>=limit?0x80:0));
    }
    PcmStatus result=record(f,'R',8,a,sample);
    if (result==PCM_OK) {
        *out=sample;if (a==PCM_ADCTL) ++f->polls;
        if (a==PCM_ADR1 && f->control==0x14 && (f->action==1 || f->action==2))
            f->pcm->reference.sample_map=f->action==1;
        if (a==PCM_PORTD && f->action==6) f->memory[a]^=0xc7;
    }
    return result;
}
static PcmStatus read16(void *v,uint16_t a,uint16_t *out)
{
    Fixture *f=v;uint16_t sample=word(f->memory,a);PcmStatus result=record(f,'R',16,a,sample);
    if (result==PCM_OK) {
        *out=sample;
        if (a==PCM_EST_COUNTER && f->action==5) {
            f->pcm->reference.latch_inhibited=true;f->pcm->reference.sample_map=true;
            f->memory[a]=0xab;f->memory[a+1]=0xcd;
        }
    }
    return result;
}
static PcmStatus write8(void *v,uint16_t a,uint8_t value)
{
    Fixture *f=v;PcmStatus result=record(f,'W',8,a,value);
    if (result==PCM_OK) {
        if (a==PCM_TFLG1) f->memory[a]&=(uint8_t)~value;else f->memory[a]=value;
        if (a==PCM_ADCTL) { f->control=value;f->polls=0; }
    }
    return result;
}
static PcmStatus write16(void *v,uint16_t a,uint16_t value)
{
    Fixture *f=v;PcmStatus result=record(f,'W',16,a,value);
    if (result==PCM_OK) { f->memory[a]=(uint8_t)(value>>8);f->memory[a+1]=(uint8_t)value; }
    return result;
}
static PcmStatus mask(void *v,bool masked)
{
    Fixture *f=v;PcmStatus result=record(f,'M',0,0,masked);
    if (result==PCM_OK) {
        f->masked=masked;
        if (!masked && f->action==3) {
            f->pcm->reference.battery=99;f->pcm->spark.battery_sample=255;f->memory[PCM_ADR4]=7;
        }
        if (masked && f->action==4) {
            f->pcm->reference.map_sample=33;f->pcm->reference.sample_map=true;
        }
    }
    return result;
}
static PcmStatus delay(void *v,uint16_t cycles) { return record(v,'D',0,0,cycles); }
static void state_transfer(Pcm *pcm,Fixture *f,bool load)
{
    transfer(pcm,f->memory,reference_state_map,SIZE(reference_state_map),load);
    transfer(pcm,f->memory,fuel_state_map,SIZE(fuel_state_map),load);
    /* Step owns only003E.2; the other fuel bits remain in coolant_context. */
    if (load) pcm->iac.low_battery=(f->memory[0x3e]&4)!=0;
    else f->memory[0x3e]=(uint8_t)((f->memory[0x3e]&0xfb)|(pcm->iac.low_battery?4:0));
}
static void init(Fixture *f,Pcm *pcm,PcmCalibration *root,PcmFuelCalibration *fuel,PcmIacCalibration *iac)
{
    memset(f,0,sizeof(*f));memset(pcm,0,sizeof(*pcm));
    *root=pcm_reference_scheduler_calibration;*fuel=pcm_reference_fuel_calibration;*iac=pcm_reference_iac_calibration;
    root->fuel=fuel;root->iac=iac;pcm->calibration=root;pcm->unresolved_task=PCM_TASK_COUNT;
    pcm->platform=&f->platform;f->pcm=pcm;
    f->platform.context=f;f->platform.read8=read8;f->platform.read16=read16;
    f->platform.write8=write8;f->platform.write16=write16;f->platform.mask_irq=mask;f->platform.delay_cycles=delay;
    transfer(root,f->memory,reference_cal_map,SIZE(reference_cal_map),false);
    transfer(fuel,f->memory,fuel_cal_map,SIZE(fuel_cal_map),false);
    f->memory[0x4eb6]=iac->step_battery_minimum;
}
static PcmStatus execute(unsigned mode,Pcm *pcm)
{
    PcmStatus result;
#define RUN(call) do { result=(call);if (result!=PCM_OK) return result; } while (0)
    switch (mode) {
    case 0:return pcm_adc_inputs(pcm);
    case 1:return pcm_adc_feedback(pcm);
    case 2:return pcm_battery_input(pcm);
    case 3:return pcm_fuel_battery_state(pcm);
    case 4:return pcm_injector_offset(pcm);
    case 5:return pcm_fuel_finalize(pcm);
    case 6:return pcm_fuel_publish(pcm,pcm->fuel.corrected_pulse);
    case 7:return pcm_fuel_async(pcm,pcm->fuel.corrected_pulse);
    case 8:RUN(pcm_battery_input(pcm));RUN(pcm_fuel_battery_state(pcm));RUN(pcm_injector_offset(pcm));return pcm_fuel_finalize(pcm);
    case 9:RUN(pcm_injector_offset(pcm));RUN(pcm_fuel_finalize(pcm));return pcm_reference_event(pcm);
    case 10:RUN(pcm_adc_inputs(pcm));RUN(pcm_reference_event(pcm));return pcm_adc_inputs(pcm);
    case 11:RUN(pcm_iac_step(pcm));return pcm_adc_feedback(pcm);
    case 12:return pcm_adc_auxiliary(pcm);
    case 13:return pcm_slot_00(pcm);
    case 14:return pcm_slot_02(pcm);
    case 15:RUN(pcm_slot_02(pcm));RUN(pcm_fuel_battery_state(pcm));RUN(pcm_injector_offset(pcm));return pcm_fuel_finalize(pcm);
    default:return PCM_BAD_CONFIGURATION;
    }
#undef RUN
}
static void contracts(void)
{
    static Fixture f;Pcm pcm;PcmCalibration root;PcmFuelCalibration fuel;PcmIacCalibration iac;
#define INIT() init(&f,&pcm,&root,&fuel,&iac)
    INIT();pcm.calibration=NULL;pcm.io.coolant_context=0x10;pcm.fuel.corrected_pulse=123;
    pcm.reference.timer_pulse=456;pcm.fuel.short_pulse=true;
    CHECK(pcm_fuel_finalize(&pcm)==PCM_OK && pcm.reference.delivered_pulse==123 && pcm.reference.timer_pulse==456 && !pcm.fuel.short_pulse && f.used==0);
    INIT();pcm.fuel.short_pulse=true;pcm.reference.additive_offset=255;
    CHECK(pcm_fuel_finalize(&pcm)==PCM_OK && pcm.fuel.short_pulse && pcm.reference.timer_pulse==0);
    INIT();pcm.reference.additive_offset=255;
    CHECK(pcm_fuel_publish(&pcm,65535)==PCM_OK && pcm.reference.delivered_pulse==65535 && pcm.reference.timer_pulse==254);
    INIT();f.platform.write16=NULL;pcm.fuel.corrected_pulse=1;
    CHECK(pcm_fuel_finalize(&pcm)==PCM_NO_HARDWARE && pcm.fuel.short_pulse && pcm.reference.delivered_pulse==32 && pcm.reference.timer_pulse==32);
    INIT();root.fuel=NULL;CHECK(pcm_fuel_publish(&pcm,100)==PCM_OK);
    root.reference.mode_b=1;CHECK(pcm_fuel_publish(&pcm,100)==PCM_BAD_CONFIGURATION && pcm.reference.timer_pulse==100);
    INIT();pcm.calibration=NULL;pcm.reference.latch_inhibited=true;pcm.spark.battery_sample=90;
    CHECK(pcm_fuel_battery_state(&pcm)==PCM_BAD_CONFIGURATION && !pcm.reference.latch_inhibited && f.used==1);
    INIT();f.platform.mask_irq=NULL;CHECK(pcm_adc_feedback(&pcm)==PCM_NO_HARDWARE && f.used==0);
    INIT();f.memory[0x900]=15;f.memory[PCM_ADR1]=255;f.memory[PCM_ADR2]=255;f.memory[PCM_ADR3]=255;f.memory[PCM_ADR4]=255;
    CHECK(pcm_adc_feedback(&pcm)==PCM_OK && pcm.fuel.measured_current==255 && !f.masked && f.used==28);
    INIT();f.memory[0x901]=12;pcm.runtime.adc_timeout=true;
    CHECK(pcm_adc_inputs(&pcm)==PCM_OK && pcm.runtime.adc_timeout && pcm.runtime.adc_fault && f.used==16);
    INIT();f.fail_at=9;pcm.reference.battery=99;
    CHECK(pcm_battery_input(&pcm)==PCM_NO_HARDWARE && pcm.reference.battery==99);
    INIT();root.fuel=NULL;pcm.reference.additive_offset=77;
    CHECK(pcm_injector_offset(&pcm)==PCM_BAD_CONFIGURATION && pcm.reference.additive_offset==77);
    INIT();f.memory[0x90a]=1;f.memory[0x90b]=12;f.memory[0x90c]=34;f.memory[0x90d]=130;
    f.memory[0x90e]=56;f.memory[0x90f]=78;pcm.reference.latch_inhibited=true;
    CHECK(execute(15,&pcm)==PCM_OK && !f.masked && pcm.io.raw_coolant==12 &&
          pcm.io.auxiliary_sample==34 && pcm.io.diagnostic_sample==56 && pcm.io.auxiliary_reference==78 &&
          pcm.spark.battery_sample==130 && !pcm.reference.latch_inhibited && pcm.reference.sample_map);
    INIT();f.memory[0x902]=12;
    CHECK(pcm_slot_02(&pcm)==PCM_OK && !f.masked && pcm.runtime.adc_fault && pcm.runtime.adc_timeout);
#undef INIT
    puts("ADC waits/timeouts, shared MAP gate, battery publication, async bypass, zero-pulse flag, wrapped offset and failed-prefix contracts pass.");
}
int main(int argc,char **argv)
{
    if (argc==2 && strcmp(argv[1],"--contracts")==0) { contracts();return 0; }
    static Fixture f;Pcm pcm;PcmCalibration root;PcmFuelCalibration fuel;PcmIacCalibration iac;
    if (argc==2 && strcmp(argv[1],"--defaults")==0) {
        init(&f,&pcm,&root,&fuel,&iac);bool first=true;printf("[");
        for (unsigned a=0x4000;a<0x6000;++a) {
            bool found=false;
            for (size_t i=0;i<SIZE(fuel_cal_map);++i) {
                const Mapping *m=&fuel_cal_map[i];unsigned n=m->width==16?2:m->count;
                if (a>=m->address && a<m->address+n) found=true;
            }
            if (found) { printf("%s[%u,%u]",first?"":",",a,f.memory[a]);first=false; }
        }
        puts("]");return 0;
    }
    uint16_t outputs[512];unsigned output_count=0;
    for (unsigned a=0;a<0x4000;++a) {
        bool found=(a>=0x3000 && a<0x3035) || (a>=0x3fc0 && a<0x3ffe);
        for (size_t k=0;k<2;++k) {
            const Mapping *map=k?fuel_state_map:reference_state_map;size_t n=k?SIZE(fuel_state_map):SIZE(reference_state_map);
            for (size_t i=0;i<n;++i) if (a>=map[i].address && a<map[i].address+(map[i].width==16?2u:1u)) found=true;
        }
        if (found) { CHECK(output_count<SIZE(outputs));outputs[output_count++]=(uint16_t)a; }
    }
    unsigned mode,count;
    while (scanf("%u %u",&mode,&count)==2) {
        CHECK(mode<16 && count<2048);init(&f,&pcm,&root,&fuel,&iac);
        for (unsigned i=0;i<count;++i) { unsigned a,v;CHECK(scanf("%u %u",&a,&v)==2 && a<65536 && v<256);f.memory[a]=(uint8_t)v; }
        state_transfer(&pcm,&f,true);
        transfer(&root,f.memory,reference_cal_map,SIZE(reference_cal_map),true);
        transfer(&fuel,f.memory,fuel_cal_map,SIZE(fuel_cal_map),true);
        iac.step_battery_minimum=f.memory[0x4eb6];
        f.fail_at=f.memory[0x907];f.action=f.memory[0x908];f.masked=f.memory[0x909]!=0;
        PcmStatus status=execute(mode,&pcm);state_transfer(&pcm,&f,false);
        CHECK(pcm.unresolved_task==PCM_TASK_COUNT);
        printf("{\"status\":%u,\"masked\":%u,\"state\":[",(unsigned)status,(unsigned)f.masked);
        bool first=true;
        for (unsigned i=0;i<output_count;++i) {
            printf("%s%u",first?"":",",f.memory[outputs[i]]);first=false;
        }
        printf("],\"events\":[");
        for (unsigned i=0;i<f.used;++i) { Event *e=&f.events[i];printf("%s[\"%c\",%u,%u,%u,%u]",i?",":"",e->kind,e->width,e->address,e->value,(unsigned)e->masked); }
        puts("]}");
    }
    return 0;
}
