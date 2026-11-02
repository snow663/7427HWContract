#define PCM_AIR_TEST_MAIN inherited_air_main
#include "fuel_air_test.c"
#undef PCM_AIR_TEST_MAIN
#include "fuel_mixture_fixture_map.h"

static PcmStatus mixture_extension(Pcm *pcm,PcmTask task)
{
    Fixture *f=pcm->application;CHECK(task==PCM_AFR_EXTENSION);
    PcmStatus result=record(f,'T',0,0x1800,0);
    if (result!=PCM_OK) return result;
    pcm->fuel.commanded_afr=f->memory[0x914];
    return (PcmStatus)f->memory[0x915];
}
static PcmStatus mixture_mask(void *v,bool masked)
{
    Fixture *f=v;PcmStatus result=mask(v,masked);
    if (result!=PCM_OK) return result;
    if (f->action==7 && masked) {
        f->pcm->fuel.pe_full_gain=true;f->pcm->reference.extra_guard=false;
        f->pcm->fuel.short_pulse=false;f->pcm->iac.startup_cancel=true;
        f->pcm->fuel.startup_context=15;f->pcm->fuel.startup_previous_rpm=255;
        f->pcm->spark.rpm_high=0;f->pcm->iac.rpm_error=255;f->pcm->iac.context|=128;
    }
    if (f->action==8 && !masked) {
        f->pcm->fuel.startup_hold=0;f->pcm->fuel.startup_afr=255;
        f->pcm->fuel.startup_park_hold=0;f->pcm->fuel.startup_interval=0;
        f->pcm->fuel.startup_context=10;f->pcm->fuel.pe_full_gain=true;
    }
    return PCM_OK;
}
static void mixture_init(Fixture *f,Pcm *pcm,PcmCalibration *root,PcmFuelCalibration *fuel,
                         PcmIacCalibration *iac,PcmAirCalibration *air,PcmIoCalibration *io,PcmMixtureCalibration *mix)
{
    air_init(f,pcm,root,fuel,iac,air,io);*mix=pcm_reference_mixture_calibration;root->mixture=mix;pcm->application=f;f->platform.mask_irq=mixture_mask;
    transfer(mix,f->memory,mixture_cal_map,SIZE(mixture_cal_map),false);f->memory[0x400d]=root->mode_d;
    for (size_t i=0;i<SIZE(mixture_tables);++i) {
        const MixtureTable *m=&mixture_tables[i];uint8_t *p=(uint8_t *)mix+m->offset;
        unsigned header=m->kind==2?3:1,capacity=m->kind==2?527:256;
        memcpy(f->memory+m->address+header,mixture_backing[i],capacity);
        const uint8_t *values;
        if (m->kind==0) { PcmScaledCurve *t=(PcmScaledCurve *)(void *)p;f->memory[m->address]=t->scale;values=t->values; }
        else if (m->kind==1) { PcmCappedCurve *t=(PcmCappedCurve *)(void *)p;f->memory[m->address]=t->limit;values=t->values; }
        else { PcmTable2D *t=(PcmTable2D *)(void *)p;f->memory[m->address]=t->row_offset;f->memory[m->address+1]=t->column_offset;f->memory[m->address+2]=t->stride;values=t->values; }
        memcpy(f->memory+m->address+header,values,m->capacity);
    }
    /* Overlapping fixture views share one bus image; source defaults are exported
     * separately, so one C profile cannot silently validate another's defaults. */
}
static void mixture_transfer(Pcm *pcm,Fixture *f,bool load)
{
    air_transfer(pcm,f,load);transfer(pcm,f->memory,mixture_state_map,SIZE(mixture_state_map),load);
    if (load) pcm->fuel.startup_context=f->memory[0x3f]&15u;
    else f->memory[0x3f]=(uint8_t)((f->memory[0x3f]&0xf0u)|(pcm->fuel.startup_context&15u));
}
static PcmStatus mixture_execute(unsigned mode,Pcm *pcm,uint16_t *value)
{
    uint8_t byte=0;bool running=false;PcmStatus result;
#define RUN(call) do { result=(call);if (result!=PCM_OK) return result; } while (0)
    switch (mode) {
    case 0:return pcm_fuel_authorize(pcm);
    case 1:return pcm_fuel_oxygen_filter(pcm);
    case 2:result=pcm_fuel_crank_coordinate(pcm,&byte);if (result==PCM_OK) *value=byte;return result;
    case 3:return pcm_fuel_crank_pulse(pcm,value);
    case 4:return pcm_fuel_crank_prepare(pcm);
    case 5:result=pcm_fuel_admit(pcm,&running);if (result==PCM_OK) *value=running;return result;
    case 6:return pcm_fuel_map_acceleration(pcm);
    case 7:return pcm_fuel_tps_acceleration(pcm);
    case 8:return pcm_fuel_acceleration(pcm);
    case 9:return pcm_fuel_transient_gains(pcm);
    case 10:return pcm_fuel_decel_history(pcm);
    case 11:return pcm_fuel_startup_seed(pcm);
    case 12:return pcm_fuel_startup_context(pcm);
    case 13:return pcm_fuel_startup_afr(pcm);
    case 14:return pcm_fuel_startup_spark(pcm);
    case 15:return pcm_fuel_startup(pcm);
    case 16:return pcm_fuel_afr_base(pcm);
    case 17:result=pcm_fuel_afr_idle(pcm,&byte);if (result==PCM_OK) *value=byte;return result;
    case 18:return pcm_fuel_afr_bias(pcm,pcm->fuel.commanded_afr);
    case 19:return pcm_fuel_pe(pcm);
    case 20:return pcm_fuel_afr_finish(pcm);
    case 21:return pcm_fuel_afr(pcm);
    case 22:RUN(pcm_fuel_transient_gains(pcm));RUN(pcm_fuel_startup(pcm));return pcm_fuel_afr(pcm);
    case 23:RUN(pcm_fuel_acceleration(pcm));return pcm_fuel_air_charge(pcm);
    case 24:RUN(pcm_fuel_afr(pcm));RUN(pcm_fuel_air_charge(pcm));return pcm_reference_event(pcm);
    case 25:RUN(pcm_fuel_decel_history(pcm));return pcm_fuel_acceleration(pcm);
    case 26:RUN(pcm_fuel_crank_prepare(pcm));return pcm_reference_event(pcm);
    default:return PCM_BAD_CONFIGURATION;
    }
#undef RUN
}
static void mixture_contracts(void)
{
    static Fixture f;Pcm pcm;PcmCalibration root;PcmFuelCalibration fuel;PcmIacCalibration iac;
    PcmAirCalibration air;PcmIoCalibration io;PcmMixtureCalibration mix;uint16_t value=0x1234;uint8_t byte=77;
#define INIT() mixture_init(&f,&pcm,&root,&fuel,&iac,&air,&io,&mix)
    INIT();root.mode_d=0;root.mixture=NULL;CHECK(pcm_fuel_authorize(&pcm)==PCM_OK && pcm.fuel.authorized && f.used==0);
    INIT();root.mode_d=0x40;root.mixture=NULL;f.memory[0x3012]=1;
    CHECK(pcm_fuel_authorize(&pcm)==PCM_BAD_CONFIGURATION && pcm.fuel.authorization_capture==256 && !pcm.fuel.authorized);
    INIT();CHECK(pcm_fuel_crank_coordinate(&pcm,NULL)==PCM_BAD_CONFIGURATION && f.used==0);
    root.mixture=NULL;CHECK(pcm_fuel_crank_coordinate(&pcm,&byte)==PCM_BAD_CONFIGURATION && byte==77 && f.used==1);
    INIT();mix.crank_base=65535;memset(mix.crank_coolant,255,17);memset(mix.crank_baro,255,11);mix.crank_tps.length=0;
    CHECK(pcm_fuel_crank_pulse(&pcm,&value)==PCM_OK && value==65535);
    mix.crank_base=10;CHECK(pcm_fuel_crank_pulse(&pcm,&value)==PCM_BAD_CONFIGURATION && value==65535);
    INIT();mix.ae_map.length=0;pcm.fuel.map_history=0;pcm.spark.load_coordinate=255;pcm.reference.throttle=255;
    CHECK(pcm_fuel_map_acceleration(&pcm)==PCM_BAD_CONFIGURATION && pcm.fuel.map_delta==255 && !pcm.fuel.map_acceleration);
    INIT();root.mixture=NULL;pcm.fuel.history_count=1;CHECK(pcm_fuel_decel_history(&pcm)==PCM_OK && pcm.fuel.history_count==0);
    CHECK(pcm_fuel_startup_context(&pcm)==PCM_BAD_CONFIGURATION && f.masked && f.used==1);
    INIT();mix.startup_spark.length=0;pcm.fuel.startup_afr=77;pcm.spark.startup_adder=99;
    CHECK(pcm_fuel_startup_seed(&pcm)==PCM_BAD_CONFIGURATION && pcm.fuel.startup_afr!=77 && pcm.spark.startup_adder==99);
    INIT();pcm.runtime.fuel_running=false;pcm.scheduler.profiling_enabled=true;
    CHECK(pcm_fuel_afr(&pcm)==PCM_OK && pcm.unresolved_task==PCM_TASK_COUNT);
    INIT();pcm.fuel.published_afr=99;pcm.reference.throttle=33;pcm.scheduler.profiling_enabled=true;
    CHECK(pcm_fuel_afr_finish(&pcm)==PCM_UNIMPLEMENTED && pcm.unresolved_task==PCM_AFR_EXTENSION && pcm.fuel.published_afr==99 && pcm.fuel.pe_previous_throttle==33);
    pcm.runtime.engine_service=true;pcm.spark.service_flags=4;pcm.fuel.service_afr=0;
    CHECK(pcm_fuel_afr_finish(&pcm)==PCM_OK && pcm.fuel.published_afr==0);
#undef INIT
    puts("Crank admission, AE histories, startup mask/failure prefixes, AFR service/extension boundaries and source-view contracts pass.");
}
#ifndef PCM_MIXTURE_TEST_MAIN
#define PCM_MIXTURE_TEST_MAIN main
#endif
int PCM_MIXTURE_TEST_MAIN(int argc,char **argv)
{
    if (argc==2 && strcmp(argv[1],"--contracts")==0) { mixture_contracts();return 0; }
    static Fixture f;Pcm pcm;PcmCalibration root;PcmFuelCalibration fuel;PcmIacCalibration iac;
    PcmAirCalibration air;PcmIoCalibration io;PcmMixtureCalibration mix;uint8_t backing[11][527],air_views[3][527];
    if (argc==2 && strcmp(argv[1],"--mixture-defaults")==0) {
        mixture_init(&f,&pcm,&root,&fuel,&iac,&air,&io,&mix);bool first=true;printf("[");
#define EMIT(a,v) do { printf("%s[%u,%u]",first?"":",",(unsigned)(a),(unsigned)(v));first=false; } while (0)
        for (size_t i=0;i<SIZE(mixture_cal_map);++i) {
            const Mapping *m=&mixture_cal_map[i];const uint8_t *p=(const uint8_t *)&mix+m->offset;
            if (m->width==16) { uint16_t v=*(const uint16_t *)(const void *)p;EMIT(m->address,v>>8);EMIT(m->address+1,v&255); }
            else for (unsigned j=0;j<m->count;++j) EMIT(m->address+j,p[j]);
        }
        for (size_t i=0;i<SIZE(mixture_tables);++i) {
            const MixtureTable *m=&mixture_tables[i];uint8_t *p=(uint8_t *)&mix+m->offset;const uint8_t *values;unsigned header=1;
            if (m->kind==0) { PcmScaledCurve *t=(PcmScaledCurve *)(void *)p;EMIT(m->address,t->scale);values=t->values; }
            else if (m->kind==1) { PcmCappedCurve *t=(PcmCappedCurve *)(void *)p;EMIT(m->address,t->limit);values=t->values; }
            else { PcmTable2D *t=(PcmTable2D *)(void *)p;header=3;EMIT(m->address,t->row_offset);EMIT(m->address+1,t->column_offset);EMIT(m->address+2,t->stride);values=t->values; }
            for (unsigned j=0;j<m->capacity;++j) EMIT(m->address+header+j,values[j]);
        }
        EMIT(0x400d,root.mode_d);puts("]");return 0;
    }
    if (argc==2 && strcmp(argv[1],"--mixture-backing")==0) {
        bool first=true;printf("[");
        for (size_t i=0;i<SIZE(mixture_tables);++i) for (unsigned j=0;j<(mixture_tables[i].kind==2?527u:256u);++j)
            EMIT(mixture_tables[i].address+(mixture_tables[i].kind==2?3:1)+j,mixture_backing[i][j]);
        puts("]");return 0;
    }
#undef EMIT
    if (argc==2) return inherited_air_main(argc,argv);
    uint16_t outputs[768];unsigned output_count=0;bool selected[0x4000]={false};
    for (unsigned a=0x3000;a<0x3035;++a) selected[a]=true;
    for (unsigned a=0x3fc0;a<0x3ffe;++a) selected[a]=true;
    for (unsigned k=0;k<4;++k) {
        const Mapping *m=k==0?reference_state_map:k==1?fuel_state_map:k==2?air_state_map:mixture_state_map;
        size_t count=k==0?SIZE(reference_state_map):k==1?SIZE(fuel_state_map):k==2?SIZE(air_state_map):SIZE(mixture_state_map);
        for (size_t i=0;i<count;++i) { selected[m[i].address]=true;if (m[i].width==16) selected[m[i].address+1]=true; }
    }
    for (unsigned a=0;a<0x4000;++a) if (selected[a]) { CHECK(output_count<SIZE(outputs));outputs[output_count++]=(uint16_t)a; }
    unsigned mode,count;
    while (scanf("%u %u",&mode,&count)==2) {
        CHECK(mode<27 && count<4096);mixture_init(&f,&pcm,&root,&fuel,&iac,&air,&io,&mix);
        for (unsigned i=0;i<count;++i) { unsigned a,v;CHECK(scanf("%u %u",&a,&v)==2 && a<65536 && v<256);f.memory[a]=(uint8_t)v; }
        mixture_transfer(&pcm,&f,true);transfer(&root,f.memory,reference_cal_map,SIZE(reference_cal_map),true);
        transfer(&fuel,f.memory,fuel_cal_map,SIZE(fuel_cal_map),true);transfer(&air,f.memory,air_cal_map,SIZE(air_cal_map),true);
        transfer(&mix,f.memory,mixture_cal_map,SIZE(mixture_cal_map),true);root.mode_d=f.memory[0x400d];
        for (size_t i=0;i<SIZE(air_tables);++i) {
            const AirTableMapping *m=&air_tables[i];PcmTable2D *t=(PcmTable2D *)(void *)((uint8_t *)&air+m->offset);
            t->row_offset=f.memory[m->address];t->column_offset=f.memory[m->address+1];t->stride=f.memory[m->address+2];
            t->length=f.memory[0x912]?527:m->capacity;memcpy(air_views[i],f.memory+m->address+3,527);t->values=air_views[i];
        }
        for (size_t i=0;i<SIZE(mixture_tables);++i) {
            const MixtureTable *m=&mixture_tables[i];uint8_t *p=(uint8_t *)&mix+m->offset;
            unsigned header=m->kind==2?3:1,n=m->kind==2?527:256;memcpy(backing[i],f.memory+m->address+header,n);
            if (m->kind==0) { PcmScaledCurve *t=(PcmScaledCurve *)(void *)p;t->scale=f.memory[m->address];t->length=f.memory[0x916]?256:m->capacity;t->values=backing[i]; }
            else if (m->kind==1) { PcmCappedCurve *t=(PcmCappedCurve *)(void *)p;t->limit=f.memory[m->address];t->length=f.memory[0x916]?17:m->capacity;t->values=backing[i]; }
            else { PcmTable2D *t=(PcmTable2D *)(void *)p;t->row_offset=f.memory[m->address];t->column_offset=f.memory[m->address+1];t->stride=f.memory[m->address+2];t->length=f.memory[0x916]?527:m->capacity;t->values=backing[i]; }
        }
        f.fail_at=f.memory[0x907];f.action=f.memory[0x908];f.masked=f.memory[0x909]!=0;
        if (f.memory[0x913]) f.platform.task[PCM_AFR_EXTENSION]=mixture_extension;
        uint16_t value=0;PcmStatus status=mixture_execute(mode,&pcm,&value);mixture_transfer(&pcm,&f,false);
        printf("{\"status\":%u,\"value\":%u,\"unresolved\":%u,\"masked\":%u,\"state\":[",(unsigned)status,(unsigned)value,(unsigned)(pcm.unresolved_task==PCM_AFR_EXTENSION),(unsigned)f.masked);
        for (unsigned i=0;i<output_count;++i) printf("%s%u",i?",":"",f.memory[outputs[i]]);
        printf("],\"events\":[");
        for (unsigned i=0;i<f.used;++i) { Event *e=&f.events[i];printf("%s[\"%c\",%u,%u,%u,%u]",i?",":"",e->kind,e->width,e->address,e->value,(unsigned)e->masked); }
        puts("]}");
    }
    return 0;
}
