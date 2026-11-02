#define PCM_FEEDBACK_TEST_MAIN inherited_feedback_main
#include "fuel_feedback_test.c"
#undef PCM_FEEDBACK_TEST_MAIN
#include "fuel_delivery_fixture_map.h"

static PcmStatus delivery_mask(void *v,bool masked)
{
    Fixture *f=v;PcmStatus result=mixture_mask(v,masked);if (result!=PCM_OK) return result;
    if (f->action==11) {
        if (masked) { f->pcm->reference.split_clear=255;f->pcm->reference.packet_updated=true;f->pcm->fuel.corrected_pulse=0x1234; }
        else { f->pcm->reference.running_packet=0;f->pcm->reference.split_clear=255;f->pcm->fuel.corrected_pulse=0x4000; }
    }
    return PCM_OK;
}
static PcmStatus delivery_delay(void *v,uint16_t cycles)
{
    Fixture *f=v;PcmStatus result=delay(v,cycles);if (result!=PCM_OK) return result;
    if (f->action==9 && cycles==11) {
        f->memory[PCM_REFERENCE_PERIOD]=0;f->memory[PCM_REFERENCE_PERIOD+1]=1;
        f->pcm->fuel.corrected_pulse=65535;f->pcm->fuel.async_accumulator_high=255;f->pcm->fuel.async_accumulator_fraction=65535;
    }
    return PCM_OK;
}
static PcmStatus delivery_read16(void *v,uint16_t a,uint16_t *out)
{
    Fixture *f=v;PcmStatus result=read16(v,a,out);if (result!=PCM_OK) return result;
    if (f->action==10 && a==PCM_REFERENCE_PERIOD) {
        f->pcm->fuel.corrected_pulse=64;f->pcm->fuel.async_accumulator_high=254;f->pcm->fuel.async_accumulator_fraction=0xff80;
    }
    return PCM_OK;
}
static PcmStatus delivery_write16(void *v,uint16_t a,uint16_t value)
{
    Fixture *f=v;PcmStatus result=write16(v,a,value);if (result!=PCM_OK) return result;
    if (f->action==12 && a==PCM_INJECTOR_WORD && value==0) f->pcm->io.coolant_context^=0x10;
    return PCM_OK;
}
static void delivery_init(Fixture *f,Pcm *pcm,PcmCalibration *root,PcmFuelCalibration *fuel,
                          PcmIacCalibration *iac,PcmAirCalibration *air,PcmIoCalibration *io,
                          PcmMixtureCalibration *mix,PcmFeedbackCalibration *feedback,PcmDeliveryCalibration *delivery)
{
    feedback_init(f,pcm,root,fuel,iac,air,io,mix,feedback);*delivery=pcm_reference_delivery_calibration;root->delivery=delivery;
    transfer(delivery,f->memory,delivery_cal_map,SIZE(delivery_cal_map),false);f->memory[0x400f]=root->mode_f;
    f->memory[0x4c94]=delivery->decel_throttle.limit;
    memcpy(f->memory+0x4c95,delivery_curve_backing,17);
    memcpy(f->memory+0x4c95,delivery->decel_throttle.values,delivery->decel_throttle.length);
    f->platform.mask_irq=delivery_mask;f->platform.delay_cycles=delivery_delay;
    f->platform.read16=delivery_read16;f->platform.write16=delivery_write16;
}
static void delivery_transfer(Pcm *pcm,Fixture *f,bool load)
{
    feedback_transfer(pcm,f,load);transfer(pcm,f->memory,delivery_state_map,SIZE(delivery_state_map),load);
}
static PcmStatus delivery_execute(unsigned mode,Pcm *pcm,uint32_t *value)
{
    bool route=false;uint16_t packet=0;PcmStatus result;
#define RUN(call) do { result=(call);if (result!=PCM_OK) return result; } while (0)
    switch (mode) {
    case 0:result=pcm_fuel_cut_gate(pcm,&route);if (result==PCM_OK) *value=route;return result;
    case 1:return pcm_fuel_acceleration_reservoir(pcm);
    case 2:result=pcm_fuel_decel_gate(pcm,&route);if (result==PCM_OK) *value=route;return result;
    case 3:return pcm_fuel_reduction(pcm);
    case 4:return pcm_fuel_enleanment(pcm);
    case 5:return pcm_fuel_cut_decel(pcm);
    case 6:return pcm_fuel_cpi_prepare(pcm);
    case 7:return pcm_fuel_async_accumulate(pcm);
    case 8:result=pcm_fuel_packet_select(pcm,&packet,&route);if (result==PCM_OK && route) *value=0x10000u|packet;return result;
    case 9:return pcm_fuel_packet_emit(pcm,pcm->fuel.corrected_pulse);
    case 10:return pcm_fuel_packet(pcm);
    case 11:result=pcm_fuel_route(pcm,&route);if (result==PCM_OK) *value=route;return result;
    case 12:return pcm_fuel_deliver(pcm);
    case 13:return pcm_fuel_construct(pcm);
    case 14:return pcm_fuel_running(pcm);
    case 15:return pcm_fuel_calculate(pcm);
    case 16:RUN(pcm_fuel_afr_learning(pcm));return pcm_fuel_calculate(pcm);
    case 17:RUN(pcm_oxygen_control(pcm));RUN(pcm_fuel_afr_learning(pcm));return pcm_fuel_calculate(pcm);
    case 18:RUN(pcm_fuel_calculate(pcm));return pcm_reference_event(pcm);
    case 19:RUN(pcm_fuel_transient_gains(pcm));RUN(pcm_fuel_startup(pcm));RUN(pcm_closed_loop_admit(pcm));
        RUN(pcm_oxygen_control(pcm));RUN(pcm_fuel_afr_learning(pcm));RUN(pcm_fuel_calculate(pcm));return pcm_reference_event(pcm);
    case 20:RUN(pcm_fuel_deliver(pcm));RUN(pcm_fuel_deliver(pcm));return pcm_fuel_deliver(pcm);
    case 21:RUN(pcm_fuel_decel_history(pcm));return pcm_fuel_running(pcm);
    default:return PCM_BAD_CONFIGURATION;
    }
#undef RUN
}
static void delivery_contracts(void)
{
    static Fixture f;Pcm pcm;PcmCalibration root;PcmFuelCalibration fuel;PcmIacCalibration iac;
    PcmAirCalibration air;PcmIoCalibration io;PcmMixtureCalibration mix;PcmFeedbackCalibration fb;PcmDeliveryCalibration dl;
    uint16_t packet=99;bool route=false;
#define INIT() delivery_init(&f,&pcm,&root,&fuel,&iac,&air,&io,&mix,&fb,&dl)
    INIT();CHECK(pcm_fuel_cut_gate(&pcm,NULL)==PCM_BAD_CONFIGURATION && f.used==0);
    CHECK(pcm_fuel_packet_select(&pcm,NULL,&route)==PCM_BAD_CONFIGURATION);
    pcm.fuel.async_accumulator_fraction=0x0180;pcm.fuel.acceleration_reservoir=1;dl.packet_minimum=2;dl.packet_maximum=100;
    CHECK(pcm_fuel_packet_select(&pcm,&packet,&route)==PCM_OK && !route && packet==99 && pcm.fuel.async_suppressed && pcm.fuel.async_accumulator_fraction==0x0180);
    INIT();pcm.fuel.async_accumulator_fraction=0x0380;pcm.fuel.acceleration_reservoir=100;dl.packet_minimum=0;dl.packet_maximum=50;f.fail_at=1;
    CHECK(pcm_fuel_packet(&pcm)==PCM_NO_HARDWARE && !f.masked && pcm.fuel.acceleration_reservoir==53 && pcm.fuel.async_accumulator_fraction==0x0080 && !pcm.fuel.async_pending);
    INIT();f.fail_at=6;CHECK(pcm_fuel_packet_emit(&pcm,100)==PCM_NO_HARDWARE && f.masked && !pcm.fuel.async_pending);
    INIT();root.reference.mode_b=0;pcm.fuel.corrected_pulse=1;dl.sync_threshold[0]=100;f.platform.delay_cycles=NULL;
    CHECK(pcm_fuel_route(&pcm,&route)==PCM_NO_HARDWARE && (pcm.io.coolant_context&0x10) && f.used==1 && f.events[0].address==PCM_INJECTOR_WORD);
    INIT();dl.decel_throttle.length=0;pcm.reference.coolant=255;pcm.spark.load_status=0;pcm.iac.park_neutral=false;
    CHECK(pcm_fuel_decel_gate(&pcm,&route)==PCM_BAD_CONFIGURATION && !route);
    INIT();pcm.reference.latch_inhibited=true;pcm.io.coolant_context=0x10;pcm.reference.timer_pulse=1234;root.delivery=NULL;
    CHECK(pcm_fuel_deliver(&pcm)==PCM_OK && pcm.fuel.corrected_pulse==0 && pcm.reference.delivered_pulse==0 && pcm.reference.timer_pulse==1234 && f.used==0);
    INIT();pcm.reference.packet_updated=true;pcm.fuel.corrected_pulse=40000;root.delivery=NULL;
    CHECK(pcm_fuel_cpi_prepare(&pcm)==PCM_OK && pcm.fuel.corrected_pulse==65535 && f.used==0);
    INIT();pcm.reference.split_clear=255;pcm.reference.running_packet=0;root.delivery=NULL;
    CHECK(pcm_fuel_cpi_prepare(&pcm)==PCM_BAD_CONFIGURATION && pcm.reference.split_clear==255 && !f.masked && f.used==2);
#undef INIT
    puts("Cut/decel bounds, packet debit/failure prefixes, fractional retention, literal masks, delay boundary, CPI reload and async bypass contracts pass.");
}
#ifndef PCM_DELIVERY_TEST_MAIN
#define PCM_DELIVERY_TEST_MAIN main
#endif
int PCM_DELIVERY_TEST_MAIN(int argc,char **argv)
{
    if (argc==2 && strcmp(argv[1],"--contracts")==0) { delivery_contracts();return 0; }
    static Fixture f;Pcm pcm;PcmCalibration root;PcmFuelCalibration fuel;PcmIacCalibration iac;
    PcmAirCalibration air;PcmIoCalibration io;PcmMixtureCalibration mix;PcmFeedbackCalibration fb;PcmDeliveryCalibration dl;uint8_t curve[17];uint8_t backing[11][527],air_views[3][527],fb_views[2][527];
    if (argc==2 && strcmp(argv[1],"--delivery-defaults")==0) {
        delivery_init(&f,&pcm,&root,&fuel,&iac,&air,&io,&mix,&fb,&dl);bool first=true;printf("[");
#define EMIT(a,v) do { printf("%s[%u,%u]",first?"":",",(unsigned)(a),(unsigned)(v));first=false; } while (0)
        for (size_t i=0;i<SIZE(delivery_cal_map);++i) {
            const Mapping *m=&delivery_cal_map[i];const uint8_t *p=(const uint8_t *)&dl+m->offset;
            if (m->width==16) { uint16_t v=*(const uint16_t *)(const void *)p;EMIT(m->address,v>>8);EMIT(m->address+1,v&255); }
            else for (unsigned j=0;j<m->count;++j) EMIT(m->address+j,p[j]);
        }
        EMIT(0x4c94,dl.decel_throttle.limit);
        for (unsigned j=0;j<dl.decel_throttle.length;++j) EMIT(0x4c95+j,dl.decel_throttle.values[j]);
        EMIT(0x400f,root.mode_f);puts("]");return 0;
    }
    if (argc==2 && strcmp(argv[1],"--delivery-backing")==0) {
        bool first=true;printf("[");for (unsigned j=0;j<17;++j) EMIT(0x4c95+j,delivery_curve_backing[j]);puts("]");return 0;
    }
#undef EMIT
    if (argc==2) return inherited_feedback_main(argc,argv);
    uint16_t outputs[768];unsigned output_count=0;bool selected[0x4000]={false};
    for (unsigned a=0x3000;a<0x3035;++a) selected[a]=true;
    for (unsigned a=0x3fc0;a<0x3ffe;++a) selected[a]=true;
    for (unsigned k=0;k<6;++k) {
        const Mapping *m=k==0?reference_state_map:k==1?fuel_state_map:k==2?air_state_map:k==3?mixture_state_map:k==4?feedback_state_map:delivery_state_map;
        size_t count=k==0?SIZE(reference_state_map):k==1?SIZE(fuel_state_map):k==2?SIZE(air_state_map):k==3?SIZE(mixture_state_map):k==4?SIZE(feedback_state_map):SIZE(delivery_state_map);
        for (size_t i=0;i<count;++i) { for (unsigned j=0;j<m[i].count;++j) selected[m[i].address+j]=true;if (m[i].width==16) selected[m[i].address+1]=true; }
    }
    for (unsigned a=0;a<0x4000;++a) if (selected[a]) { CHECK(output_count<SIZE(outputs));outputs[output_count++]=(uint16_t)a; }
    unsigned mode,count;
    while (scanf("%u %u",&mode,&count)==2) {
        CHECK(mode<22 && count<4096);delivery_init(&f,&pcm,&root,&fuel,&iac,&air,&io,&mix,&fb,&dl);
        for (unsigned i=0;i<count;++i) { unsigned a,v;CHECK(scanf("%u %u",&a,&v)==2 && a<65536 && v<256);f.memory[a]=(uint8_t)v; }
        delivery_transfer(&pcm,&f,true);transfer(&root,f.memory,reference_cal_map,SIZE(reference_cal_map),true);
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
        transfer(&dl,f.memory,delivery_cal_map,SIZE(delivery_cal_map),true);root.mode_f=f.memory[0x400f];
        memcpy(curve,f.memory+0x4c95,17);dl.decel_throttle.limit=f.memory[0x4c94];
        dl.decel_throttle.length=f.memory[0x916]?17:pcm_reference_delivery_calibration.decel_throttle.length;dl.decel_throttle.values=curve;
        f.fail_at=f.memory[0x907];f.action=f.memory[0x908];f.masked=f.memory[0x909]!=0;
        if (f.memory[0x913]) f.platform.task[PCM_AFR_EXTENSION]=mixture_extension;
        uint32_t value=0;PcmStatus status=delivery_execute(mode,&pcm,&value);delivery_transfer(&pcm,&f,false);
        printf("{\"status\":%u,\"value\":%u,\"unresolved\":%u,\"masked\":%u,\"state\":[",(unsigned)status,(unsigned)value,(unsigned)(pcm.unresolved_task==PCM_AFR_EXTENSION),(unsigned)f.masked);
        for (unsigned i=0;i<output_count;++i) printf("%s%u",i?",":"",f.memory[outputs[i]]);
        printf("],\"events\":[");
        for (unsigned i=0;i<f.used;++i) { Event *e=&f.events[i];printf("%s[\"%c\",%u,%u,%u,%u]",i?",":"",e->kind,e->width,e->address,e->value,(unsigned)e->masked); }
        puts("]}");
    }
    return 0;
}
