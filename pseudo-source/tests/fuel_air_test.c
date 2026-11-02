#define main inherited_fuel_output_main
#include "fuel_output_test.c"
#undef main
#include "board_io.h"
#include "spark.h"
#include "fuel_air_fixture_map.h"

static PcmStatus air_read8(void *v,uint16_t a,uint8_t *out)
{
    Fixture *f=v;
    unsigned mux=(f->memory[PCM_PORTD]>>3)&7u;
    if (a==PCM_ADR4 && (f->memory[0x90a]&2u) && (mux==4 || mux==5)) {
        uint8_t saved=f->memory[a];f->memory[a]=f->memory[mux==4?0x910:0x911];
        PcmStatus result=read8(v,a,out);f->memory[a]=saved;return result;
    }
    return read8(v,a,out);
}
static void air_init(Fixture *f,Pcm *pcm,PcmCalibration *root,PcmFuelCalibration *fuel,
                     PcmIacCalibration *iac,PcmAirCalibration *air,PcmIoCalibration *io)
{
    init(f,pcm,root,fuel,iac);*air=pcm_reference_air_calibration;*io=pcm_reference_io_calibration;
    root->air=air;root->io=io;f->platform.read8=air_read8;
    for (size_t i=0;i<SIZE(air_tables);++i) memcpy(f->memory+air_tables[i].address+3,air_backing[i],527);
    transfer(air,f->memory,air_cal_map,SIZE(air_cal_map),false);
    memcpy(f->memory+0xfc45,air->coolant_table,512);f->memory[0x4e68]=io->map_default;
    for (size_t i=0;i<SIZE(air_tables);++i) {
        const AirTableMapping *m=&air_tables[i];
        const PcmTable2D *t=(const PcmTable2D *)(const void *)((const uint8_t *)air+m->offset);
        CHECK(t->length==m->capacity);f->memory[m->address]=t->row_offset;
        f->memory[m->address+1]=t->column_offset;f->memory[m->address+2]=t->stride;
        memcpy(f->memory+m->address+3,t->values,t->length);
    }
}
static void air_transfer(Pcm *pcm,Fixture *f,bool load)
{
    state_transfer(pcm,f,load);transfer(pcm,f->memory,air_state_map,SIZE(air_state_map),load);
}
static PcmStatus air_execute(unsigned mode,Pcm *pcm,uint8_t *value)
{
    PcmStatus result;
#define RUN(call) do { result=(call);if (result!=PCM_OK) return result; } while (0)
    switch (mode) {
    case 0:return pcm_throttle_zero(pcm);
    case 1:return pcm_throttle_normalize(pcm,value);
    case 2:return pcm_fuel_throttle(pcm);
    case 3:return pcm_coolant_input(pcm);
    case 4:return pcm_mat_input(pcm);
    case 5:return pcm_baro_input(pcm);
    case 6:return pcm_fuel_density(pcm);
    case 7:return pcm_fuel_charge_temperature(pcm);
    case 8:return pcm_fuel_ve(pcm);
    case 9:return pcm_fuel_base_publish(pcm);
    case 10:return pcm_fuel_air_charge(pcm);
    case 11:RUN(pcm_throttle_zero(pcm));return pcm_fuel_throttle(pcm);
    case 12:RUN(pcm_coolant_input(pcm));RUN(pcm_mat_input(pcm));RUN(pcm_baro_input(pcm));
        RUN(pcm_fuel_density(pcm));RUN(pcm_spark_load(pcm));RUN(pcm_fuel_charge_temperature(pcm));
        RUN(pcm_fuel_air_charge(pcm));return pcm_fuel_finalize(pcm);
    case 13:RUN(pcm_adc_auxiliary(pcm));RUN(pcm_coolant_input(pcm));RUN(pcm_mat_input(pcm));
        RUN(pcm_baro_input(pcm));RUN(pcm_fuel_density(pcm));RUN(pcm_spark_load(pcm));
        RUN(pcm_fuel_throttle(pcm));RUN(pcm_fuel_charge_temperature(pcm));RUN(pcm_fuel_air_charge(pcm));
        RUN(pcm_injector_offset(pcm));return pcm_fuel_finalize(pcm);
    case 14:RUN(pcm_fuel_charge_temperature(pcm));return pcm_injector_offset(pcm);
    case 15:RUN(pcm_coolant_input(pcm));return pcm_environment_inputs(pcm);
    case 16:RUN(pcm_fuel_air_charge(pcm));return pcm_reference_event(pcm);
    case 17:RUN(pcm_fuel_charge_temperature(pcm));RUN(pcm_fuel_air_charge(pcm));
        RUN(pcm_fuel_charge_temperature(pcm));return pcm_fuel_air_charge(pcm);
    default:return PCM_BAD_CONFIGURATION;
    }
#undef RUN
}
static void air_contracts(void)
{
    static Fixture f;Pcm pcm;PcmCalibration root;PcmFuelCalibration fuel;PcmIacCalibration iac;
    PcmAirCalibration air;PcmIoCalibration io;uint8_t value=77;
#define INIT() air_init(&f,&pcm,&root,&fuel,&iac,&air,&io)
    INIT();pcm.calibration=NULL;pcm.fuel.raw_throttle=10;pcm.iac.tps_zero_high=10;
    CHECK(pcm_throttle_zero(&pcm)==PCM_OK);pcm.fuel.raw_throttle=11;
    CHECK(pcm_throttle_zero(&pcm)==PCM_BAD_CONFIGURATION);
    INIT();pcm.reference.throttle=99;root.air=NULL;
    CHECK(pcm_fuel_throttle(&pcm)==PCM_BAD_CONFIGURATION && pcm.spark.previous_throttle==99);
    INIT();CHECK(pcm_throttle_normalize(&pcm,NULL)==PCM_BAD_CONFIGURATION);
    pcm.iac.tps_zero_high=255;pcm.iac.tps_zero_low=255;pcm.fuel.raw_throttle=1;air.throttle_gain=255;
    CHECK(pcm_throttle_normalize(&pcm,&value)==PCM_OK && value==4);
    INIT();pcm.fuel.open_ve=false;pcm.fuel.volumetric_efficiency=77;pcm.reference.throttle=255;air.ve_open.length=0;
    CHECK(pcm_fuel_ve(&pcm)==PCM_BAD_CONFIGURATION && pcm.fuel.open_ve && pcm.fuel.volumetric_efficiency==77);
    INIT();pcm.fuel.open_ve=true;pcm.fuel.ve_reset_request=false;pcm.reference.rpm_coordinate=0;
    pcm.reference.throttle=0;pcm.spark.vehicle_speed_high=0;air.ve_idle.length=0;
    CHECK(pcm_fuel_ve(&pcm)==PCM_BAD_CONFIGURATION && pcm.fuel.open_ve && !pcm.fuel.ve_reset_request);
    INIT();pcm.reference.latch_inhibited=false;pcm.spark.map_filtered=0;pcm.spark.barometric_high=100;
    pcm.reference.coolant=255;pcm.reference.throttle=200;pcm.fuel.throttle_decel_filter=200u<<8;
    pcm.spark.rpm_low_coordinate=100;air.baro_correction.length=0;
    CHECK(pcm_baro_input(&pcm)==PCM_BAD_CONFIGURATION && pcm.spark.barometric_high==100 && f.used==0);
    INIT();air.mat_runtime_limit=0;root.air=NULL;f.memory[PCM_ADR4]=50;
    CHECK(pcm_mat_input(&pcm)==PCM_BAD_CONFIGURATION && pcm.io.mat_raw==205 && !f.masked);
    INIT();air.baro_options=4;f.fail_at=9;pcm.io.barometric_sample=99;
    CHECK(pcm_baro_input(&pcm)==PCM_NO_HARDWARE && pcm.io.barometric_sample==99);
    INIT();pcm.fuel.displaced=11;pcm.fuel.air_charge=22;root.air=NULL;
    CHECK(pcm_fuel_base_publish(&pcm)==PCM_BAD_CONFIGURATION && pcm.fuel.displaced==11 && pcm.fuel.air_charge==22);
    INIT();pcm.fuel.charge_temperature=0;pcm.spark.density=65535;pcm.fuel.commanded_afr=0;
    pcm.fuel.volumetric_efficiency=255;pcm.spark.period=0;air.injector_flow=0;
    CHECK(pcm_fuel_base_publish(&pcm)==PCM_OK && pcm.iac.runtime_high==255 &&
          pcm.fuel.air_rate_fraction==255 && pcm.fuel.corrected_pulse==65535);
#undef INIT
    puts("TPS fractional zero, coolant ranges, MAT prefix/retention, BARO view bounds, VE flag prefixes and live fuel publication contracts pass.");
}
int main(int argc,char **argv)
{
    if (argc==2 && strcmp(argv[1],"--contracts")==0) { air_contracts();return 0; }
    static Fixture f;Pcm pcm;PcmCalibration root;PcmFuelCalibration fuel;PcmIacCalibration iac;
    PcmAirCalibration air;PcmIoCalibration io;uint8_t backing[3][527];
    if (argc==2 && strcmp(argv[1],"--air-defaults")==0) {
        air_init(&f,&pcm,&root,&fuel,&iac,&air,&io);bool first=true;printf("[");
#define EMIT(a,v) do { printf("%s[%u,%u]",first?"":",",(unsigned)(a),(unsigned)(v));first=false; } while (0)
        for (size_t i=0;i<SIZE(air_cal_map);++i) {
            const Mapping *m=&air_cal_map[i];const uint8_t *p=(const uint8_t *)&air+m->offset;
            if (m->width==16) { uint16_t v=*(const uint16_t *)(const void *)p;EMIT(m->address,v>>8);EMIT(m->address+1,v&255); }
            else for (unsigned j=0;j<m->count;++j) EMIT(m->address+j,p[j]);
        }
        for (unsigned i=0;i<512;++i) EMIT(0xfc45+i,((const uint8_t *)air.coolant_table)[i]);
        for (size_t i=0;i<SIZE(air_tables);++i) {
            const AirTableMapping *m=&air_tables[i];const PcmTable2D *t=(const PcmTable2D *)(const void *)((const uint8_t *)&air+m->offset);
            EMIT(m->address,t->row_offset);EMIT(m->address+1,t->column_offset);EMIT(m->address+2,t->stride);
            for (unsigned j=0;j<t->length;++j) EMIT(m->address+3+j,t->values[j]);
        }
        EMIT(0x4e68,io.map_default);puts("]");return 0;
    }
    if (argc==2 && strcmp(argv[1],"--air-backing")==0) {
        bool first=true;printf("[");
        for (size_t i=0;i<SIZE(air_tables);++i) for (unsigned j=0;j<527;++j) EMIT(air_tables[i].address+3+j,air_backing[i][j]);
        puts("]");return 0;
    }
#undef EMIT
    if (argc==2) return inherited_fuel_output_main(argc,argv);
    uint16_t outputs[512];unsigned output_count=0;
    bool selected[0x4000]={false};
    for (unsigned a=0x3000;a<0x3035;++a) selected[a]=true;
    for (unsigned a=0x3fc0;a<0x3ffe;++a) selected[a]=true;
    for (unsigned k=0;k<3;++k) {
        const Mapping *m=k==0?reference_state_map:k==1?fuel_state_map:air_state_map;
        size_t count=k==0?SIZE(reference_state_map):k==1?SIZE(fuel_state_map):SIZE(air_state_map);
        for (size_t i=0;i<count;++i) { selected[m[i].address]=true;if (m[i].width==16) selected[m[i].address+1]=true; }
    }
    for (unsigned a=0;a<0x4000;++a) if (selected[a]) { CHECK(output_count<SIZE(outputs));outputs[output_count++]=(uint16_t)a; }
    unsigned mode,count;
    while (scanf("%u %u",&mode,&count)==2) {
        CHECK(mode<18 && count<4096);air_init(&f,&pcm,&root,&fuel,&iac,&air,&io);
        for (unsigned i=0;i<count;++i) { unsigned a,v;CHECK(scanf("%u %u",&a,&v)==2 && a<65536 && v<256);f.memory[a]=(uint8_t)v; }
        air_transfer(&pcm,&f,true);
        transfer(&root,f.memory,reference_cal_map,SIZE(reference_cal_map),true);
        transfer(&fuel,f.memory,fuel_cal_map,SIZE(fuel_cal_map),true);
        transfer(&air,f.memory,air_cal_map,SIZE(air_cal_map),true);
        memcpy(air.coolant_table,f.memory+0xfc45,512);io.map_default=f.memory[0x4e68];
        for (size_t i=0;i<SIZE(air_tables);++i) {
            const AirTableMapping *m=&air_tables[i];PcmTable2D *t=(PcmTable2D *)(void *)((uint8_t *)&air+m->offset);
            t->row_offset=f.memory[m->address];t->column_offset=f.memory[m->address+1];t->stride=f.memory[m->address+2];
            t->length=f.memory[0x912]?527:m->capacity;memcpy(backing[i],f.memory+m->address+3,527);t->values=backing[i];
        }
        f.fail_at=f.memory[0x907];f.action=f.memory[0x908];f.masked=f.memory[0x909]!=0;
        uint8_t value=0;PcmStatus status=air_execute(mode,&pcm,&value);air_transfer(&pcm,&f,false);
        CHECK(pcm.unresolved_task==PCM_TASK_COUNT);
        printf("{\"status\":%u,\"value\":%u,\"masked\":%u,\"state\":[",(unsigned)status,(unsigned)value,(unsigned)f.masked);
        for (unsigned i=0;i<output_count;++i) printf("%s%u",i?",":"",f.memory[outputs[i]]);
        printf("],\"events\":[");
        for (unsigned i=0;i<f.used;++i) { Event *e=&f.events[i];printf("%s[\"%c\",%u,%u,%u,%u]",i?",":"",e->kind,e->width,e->address,e->value,(unsigned)e->masked); }
        puts("]}");
    }
    return 0;
}
