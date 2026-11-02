#define PCM_MIXTURE_TEST_MAIN inherited_mixture_main
#include "fuel_mixture_test.c"
#undef PCM_MIXTURE_TEST_MAIN
#include "fuel_feedback_fixture_map.h"

static void feedback_init(Fixture *f,Pcm *pcm,PcmCalibration *root,PcmFuelCalibration *fuel,
                          PcmIacCalibration *iac,PcmAirCalibration *air,PcmIoCalibration *io,
                          PcmMixtureCalibration *mix,PcmFeedbackCalibration *feedback)
{
    mixture_init(f,pcm,root,fuel,iac,air,io,mix);*feedback=pcm_reference_feedback_calibration;root->feedback=feedback;
    transfer(feedback,f->memory,feedback_cal_map,SIZE(feedback_cal_map),false);
    for (size_t i=0;i<SIZE(feedback_tables);++i) {
        const AirTableMapping *m=&feedback_tables[i];
        const PcmTable2D *t=(const PcmTable2D *)(const void *)((const uint8_t *)feedback+m->offset);
        CHECK(t->length==m->capacity);memcpy(f->memory+m->address+3,feedback_backing[i],527);
        f->memory[m->address]=t->row_offset;f->memory[m->address+1]=t->column_offset;f->memory[m->address+2]=t->stride;
        memcpy(f->memory+m->address+3,t->values,t->length);
    }
}
static void feedback_transfer(Pcm *pcm,Fixture *f,bool load)
{
    mixture_transfer(pcm,f,load);transfer(pcm,f->memory,feedback_state_map,SIZE(feedback_state_map),load);
}
static PcmStatus feedback_execute(unsigned mode,Pcm *pcm,uint16_t *value,uint8_t input)
{
    uint8_t byte=0;bool admitted=false;PcmStatus result;
#define RUN(call) do { result=(call);if (result!=PCM_OK) return result; } while (0)
    switch (mode) {
    case 0:return pcm_oxygen_activity(pcm);
    case 1:return pcm_closed_loop_admit(pcm);
    case 2:return pcm_oxygen_thresholds(pcm);
    case 3:return pcm_oxygen_direction(pcm);
    case 4:return pcm_oxygen_neutral(pcm);
    case 5:result=pcm_oxygen_admit(pcm,&admitted);if (result==PCM_OK) *value=admitted;return result;
    case 6:result=pcm_oxygen_proportional(pcm,&byte);if (result==PCM_OK) *value=byte;return result;
    case 7:return pcm_oxygen_integrator(pcm);
    case 8:return pcm_oxygen_window(pcm,input);
    case 9:return pcm_oxygen_combine(pcm);
    case 10:return pcm_oxygen_control(pcm);
    case 11:return pcm_blm_reset(pcm);
    case 12:return pcm_blm_boot_clamp(pcm);
    case 13:return pcm_blm_select(pcm);
    case 14:return pcm_blm_transition(pcm);
    case 15:return pcm_blm_learn(pcm);
    case 16:return pcm_blm_control(pcm);
    case 17:return pcm_fuel_afr_learning(pcm);
    case 18:return pcm_fuel_pulse_scale(pcm,input);
    case 19:return pcm_fuel_blm_scale(pcm,input);
    case 20:return pcm_fuel_egr_blm(pcm);
    case 21:return pcm_fuel_derivative_correction(pcm);
    case 22:return pcm_fuel_baro_battery(pcm);
    case 23:return pcm_fuel_feedback_apply(pcm);
    case 24:return pcm_fuel_post_corrections(pcm);
    case 25:RUN(pcm_fuel_oxygen_filter(pcm));return pcm_oxygen_control(pcm);
    case 26:RUN(pcm_fuel_afr_learning(pcm));return pcm_fuel_egr_blm(pcm);
    case 27:RUN(pcm_oxygen_control(pcm));RUN(pcm_fuel_afr_learning(pcm));RUN(pcm_fuel_air_charge(pcm));
        RUN(pcm_fuel_egr_blm(pcm));RUN(pcm_fuel_post_corrections(pcm));return pcm_fuel_finalize(pcm);
    case 28:RUN(pcm_fuel_startup(pcm));RUN(pcm_closed_loop_admit(pcm));return pcm_fuel_afr_learning(pcm);
    case 29:RUN(pcm_blm_boot_clamp(pcm));return pcm_blm_control(pcm);
    case 30:RUN(pcm_oxygen_control(pcm));RUN(pcm_fuel_post_corrections(pcm));RUN(pcm_fuel_finalize(pcm));return pcm_reference_event(pcm);
    default:return PCM_BAD_CONFIGURATION;
    }
#undef RUN
}
static void feedback_contracts(void)
{
    static Fixture f;Pcm pcm;PcmCalibration root;PcmFuelCalibration fuel;PcmIacCalibration iac;
    PcmAirCalibration air;PcmIoCalibration io;PcmMixtureCalibration mix;PcmFeedbackCalibration fb;uint8_t window=77;
#define INIT() feedback_init(&f,&pcm,&root,&fuel,&iac,&air,&io,&mix,&fb)
    INIT();memset((void *)pcm.fuel.blm_cells,255,21);pcm.iac.blm_value=99;pcm.iac.blm_cell_index=20;
    CHECK(pcm_blm_reset(&pcm)==PCM_OK && pcm.iac.blm_value==99 && pcm.iac.blm_cell_index==20);
    for (unsigned i=0;i<21;++i) CHECK(pcm.fuel.blm_cells[i]==128);
    fb.boot_maximum=10;fb.boot_minimum=200;CHECK(pcm_blm_boot_clamp(&pcm)==PCM_OK);
    for (unsigned i=0;i<21;++i) CHECK(pcm.fuel.blm_cells[i]==200);
    INIT();pcm.fuel.oxygen_filtered=0x12ff;pcm.fuel.feedback_encoded=99;CHECK(pcm_oxygen_neutral(&pcm)==PCM_OK);
    CHECK(pcm.fuel.oxygen_filtered==0x66ff && pcm.fuel.integrator==128 && pcm.fuel.feedback_encoded==0);
    INIT();CHECK(pcm_oxygen_proportional(&pcm,NULL)==PCM_BAD_CONFIGURATION && f.used==0);
    pcm.spark.idle_state=true;pcm.fuel.oxygen_filtered=0;pcm.fuel.oxygen_lower=0;pcm.io.coolant_context=0;
    memset(fb.error_curve,128,sizeof(fb.error_curve));f.fail_at=2;
    CHECK(pcm_oxygen_proportional(&pcm,&window)==PCM_NO_HARDWARE && f.masked && window==77 && pcm.fuel.proportional==128 && pcm.fuel.startup_context==5);
    INIT();pcm.io.coolant_context=0;root.feedback=NULL;CHECK(pcm_oxygen_admit(&pcm,NULL)==PCM_BAD_CONFIGURATION);
    pcm.runtime.fuel_running=false;CHECK(pcm_closed_loop_admit(&pcm)==PCM_OK && f.used==0);
    INIT();pcm.io.coolant_context=0x42;pcm.fuel.integrator=0;pcm.iac.blm_cell_index=21;fb.learning_delay=0;fb.learning_error[1]=0;
    CHECK(pcm_blm_learn(&pcm)==PCM_BAD_CONFIGURATION && pcm.fuel.blm_interval_count==1 && pcm.fuel.blm_learning_count==1);
    INIT();fb.baro.length=0;pcm.fuel.corrected_pulse=999;
    CHECK(pcm_fuel_baro_battery(&pcm)==PCM_BAD_CONFIGURATION && pcm.fuel.corrected_pulse==999);
    INIT();pcm.fuel.corrected_pulse=40000;CHECK(pcm_fuel_blm_scale(&pcm,128)==PCM_OK && pcm.fuel.corrected_pulse==32768);
    pcm.fuel.feedback_encoded=255;pcm.fuel.map_ae=0;CHECK(pcm_fuel_feedback_apply(&pcm)==PCM_OK && pcm.fuel.corrected_pulse==32767 && pcm.reference.running_packet==32767);
    INIT();pcm.scheduler.profiling_enabled=true;pcm.runtime.fuel_running=true;pcm.fuel.blm_previous=99;
    CHECK(pcm_fuel_afr_learning(&pcm)==PCM_UNIMPLEMENTED && pcm.unresolved_task==PCM_AFR_EXTENSION && pcm.fuel.blm_previous==99);
#undef INIT
    puts("O2 neutral fraction, literal-mask prefixes, BLM reset/boot/index bounds, saturated multiply, signed addition and extension-stop contracts pass.");
}
#ifndef PCM_FEEDBACK_TEST_MAIN
#define PCM_FEEDBACK_TEST_MAIN main
#endif
int PCM_FEEDBACK_TEST_MAIN(int argc,char **argv)
{
    if (argc==2 && strcmp(argv[1],"--contracts")==0) { feedback_contracts();return 0; }
    static Fixture f;Pcm pcm;PcmCalibration root;PcmFuelCalibration fuel;PcmIacCalibration iac;
    PcmAirCalibration air;PcmIoCalibration io;PcmMixtureCalibration mix;PcmFeedbackCalibration fb;uint8_t backing[11][527],air_views[3][527],fb_views[2][527];
    if (argc==2 && strcmp(argv[1],"--feedback-defaults")==0) {
        feedback_init(&f,&pcm,&root,&fuel,&iac,&air,&io,&mix,&fb);bool first=true;printf("[");
#define EMIT(a,v) do { printf("%s[%u,%u]",first?"":",",(unsigned)(a),(unsigned)(v));first=false; } while (0)
        for (size_t i=0;i<SIZE(feedback_cal_map);++i) {
            const Mapping *m=&feedback_cal_map[i];const uint8_t *p=(const uint8_t *)&fb+m->offset;
            for (unsigned j=0;j<m->count;++j) EMIT(m->address+j,p[j]);
        }
        for (size_t i=0;i<SIZE(feedback_tables);++i) {
            const AirTableMapping *m=&feedback_tables[i];const PcmTable2D *t=(const PcmTable2D *)(const void *)((const uint8_t *)&fb+m->offset);
            EMIT(m->address,t->row_offset);EMIT(m->address+1,t->column_offset);EMIT(m->address+2,t->stride);
            for (unsigned j=0;j<t->length;++j) EMIT(m->address+3+j,t->values[j]);
        }
        puts("]");return 0;
    }
    if (argc==2 && strcmp(argv[1],"--feedback-backing")==0) {
        bool first=true;printf("[");
        for (size_t i=0;i<SIZE(feedback_tables);++i) for (unsigned j=0;j<527;++j) EMIT(feedback_tables[i].address+3+j,feedback_backing[i][j]);
        puts("]");return 0;
    }
#undef EMIT
    if (argc==2) return inherited_mixture_main(argc,argv);
    uint16_t outputs[768];unsigned output_count=0;bool selected[0x4000]={false};
    for (unsigned a=0x3000;a<0x3035;++a) selected[a]=true;
    for (unsigned a=0x3fc0;a<0x3ffe;++a) selected[a]=true;
    for (unsigned k=0;k<5;++k) {
        const Mapping *m=k==0?reference_state_map:k==1?fuel_state_map:k==2?air_state_map:k==3?mixture_state_map:feedback_state_map;
        size_t count=k==0?SIZE(reference_state_map):k==1?SIZE(fuel_state_map):k==2?SIZE(air_state_map):k==3?SIZE(mixture_state_map):SIZE(feedback_state_map);
        for (size_t i=0;i<count;++i) { for (unsigned j=0;j<m[i].count;++j) selected[m[i].address+j]=true;if (m[i].width==16) selected[m[i].address+1]=true; }
    }
    for (unsigned a=0;a<0x4000;++a) if (selected[a]) { CHECK(output_count<SIZE(outputs));outputs[output_count++]=(uint16_t)a; }
    unsigned mode,count;
    while (scanf("%u %u",&mode,&count)==2) {
        CHECK(mode<31 && count<4096);feedback_init(&f,&pcm,&root,&fuel,&iac,&air,&io,&mix,&fb);
        for (unsigned i=0;i<count;++i) { unsigned a,v;CHECK(scanf("%u %u",&a,&v)==2 && a<65536 && v<256);f.memory[a]=(uint8_t)v; }
        feedback_transfer(&pcm,&f,true);transfer(&root,f.memory,reference_cal_map,SIZE(reference_cal_map),true);
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
        transfer(&fb,f.memory,feedback_cal_map,SIZE(feedback_cal_map),true);
        for (size_t i=0;i<SIZE(feedback_tables);++i) {
            const AirTableMapping *m=&feedback_tables[i];PcmTable2D *t=(PcmTable2D *)(void *)((uint8_t *)&fb+m->offset);
            t->row_offset=f.memory[m->address];t->column_offset=f.memory[m->address+1];t->stride=f.memory[m->address+2];
            t->length=f.memory[0x916]?527:m->capacity;memcpy(fb_views[i],f.memory+m->address+3,527);t->values=fb_views[i];
        }
        f.fail_at=f.memory[0x907];f.action=f.memory[0x908];f.masked=f.memory[0x909]!=0;
        if (f.memory[0x913]) f.platform.task[PCM_AFR_EXTENSION]=mixture_extension;
        uint16_t value=0;PcmStatus status=feedback_execute(mode,&pcm,&value,f.memory[0x917]);feedback_transfer(&pcm,&f,false);
        printf("{\"status\":%u,\"value\":%u,\"unresolved\":%u,\"masked\":%u,\"state\":[",(unsigned)status,(unsigned)value,(unsigned)(pcm.unresolved_task==PCM_AFR_EXTENSION),(unsigned)f.masked);
        for (unsigned i=0;i<output_count;++i) printf("%s%u",i?",":"",f.memory[outputs[i]]);
        printf("],\"events\":[");
        for (unsigned i=0;i<f.used;++i) { Event *e=&f.events[i];printf("%s[\"%c\",%u,%u,%u,%u]",i?",":"",e->kind,e->width,e->address,e->value,(unsigned)e->masked); }
        puts("]}");
    }
    return 0;
}
