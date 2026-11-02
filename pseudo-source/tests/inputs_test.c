#define IO_FIXTURE_ENTRY inherited_io_fixture_main
#include "io_test.c"
#include "inputs_fixture_map.h"
#define MAPSIZE(a) (sizeof(a)/sizeof((a)[0]))
static void input_state_transfer(Pcm *pcm,Fixture *f,bool load)
{
    for (size_t i=0;i<MAPSIZE(input_state_map);++i) {
        const Mapping *m=&input_state_map[i];
        if (m->width==7) {
            volatile uint8_t *p=(volatile uint8_t *)(void *)((uint8_t *)pcm+m->offset);
            if (load) *p=f->memory[m->address]&m->mask;
            else f->memory[m->address]=(uint8_t)((f->memory[m->address]&~m->mask)|(*p&m->mask));
        } else transfer(pcm,f->memory,m,1,load);
    }
}
static PcmStatus input_read16(void *context,uint16_t address,uint16_t *value)
{
    if (address!=PCM_SHIFT_COUNTER) return io_read16(context,address,value);
    Fixture *f=context;uint16_t sample=word(f->memory,address);
    PcmStatus result=record(f,'R',16,address,sample);
    if (result==PCM_OK) {
        *value=sample;
        if (f->action==44) { f->pcm->transmission.shift_counter=0xabcd;f->memory[address]=0x12;f->memory[address+1]=0x34; }
    }
    return result;
}
static PcmStatus input_mask(void *context,bool masked)
{
    Fixture *f=context;PcmStatus result=io_mask(context,masked);
    if (result==PCM_OK && masked && f->action==45) { f->pcm->io.diagnostic_sample=50;f->pcm->runtime.factory_mode=true; }
    if (result==PCM_OK && !masked && f->action==46) {
        ((PcmCalibration *)(void *)f->pcm->calibration)->mode_f=4;
        f->pcm->iac.input_shadow=0;f->pcm->io.ac_entry=77;f->pcm->io.ac_exit=88;
    }
    return result;
}
static void input_init(Fixture *f,Pcm *pcm,PcmCalibration *root,PcmSparkCalibration *spark,
        PcmTransmissionCalibration *transmission,uint8_t *patterns,PcmIacCalibration *iac,PcmIoCalibration *io,
        PcmAcCalibration *ac,PcmEnvironmentCalibration *environment)
{
    io_init(f,pcm,root,spark,transmission,patterns,iac,io);
    *ac=pcm_reference_ac_calibration;*environment=pcm_reference_environment_calibration;
    root->ac=ac;root->environment=environment;f->memory[0x400e]=root->reference.mode_e;
    transfer(root,f->memory,input_knock_map,MAPSIZE(input_knock_map),false);
    transfer(io,f->memory,input_io_map,MAPSIZE(input_io_map),false);
    transfer(ac,f->memory,input_ac_map,MAPSIZE(input_ac_map),false);
    transfer(environment,f->memory,input_environment_map,MAPSIZE(input_environment_map),false);
    transfer(transmission,f->memory,input_transmission_map,MAPSIZE(input_transmission_map),false);
    memcpy(f->memory+0x4760,input_density_backing,12);
    f->platform.read16=input_read16;f->platform.mask_irq=input_mask;
    f->platform.task[PCM_AC_SWITCH_INPUTS]=f->platform.task[PCM_SHIFT_LAMP]=f->platform.task[PCM_VSS_FILTER]=NULL;
}
static void input_contracts(void)
{
    static Fixture f;Pcm pcm;PcmCalibration root;PcmSparkCalibration spark;
    PcmTransmissionCalibration transmission;PcmIacCalibration iac;PcmIoCalibration io;
    PcmAcCalibration ac;PcmEnvironmentCalibration environment;uint8_t patterns[256];
#define INIT() input_init(&f,&pcm,&root,&spark,&transmission,patterns,&iac,&io,&ac,&environment)
    INIT();pcm.io.coolant_context=0xa0;pcm.spark.idle_state=true;pcm.io.map_hold=1;
    CHECK(pcm_map_transient(&pcm)==PCM_OK && pcm.io.map_transient && pcm.io.map_hold==0);
    CHECK(pcm_map_transient(&pcm)==PCM_OK && !pcm.io.map_transient);
    pcm.io.coolant_context=0x20;CHECK(pcm_map_transient(&pcm)==PCM_OK && !pcm.io.map_transient);
    pcm.io.coolant_context=0;CHECK(pcm_map_transient(&pcm)==PCM_OK && pcm.io.map_transient && pcm.io.map_hold==64);
    INIT();pcm.calibration=NULL;pcm.io.vss_changes=1;pcm.io.vss_raw=0x1234;pcm.io.vss_timestamp=99;
    CHECK(pcm_vss_calculate(&pcm)==PCM_OK && pcm.io.vss_raw==0x1234 && pcm.io.vss_previous==99 && pcm.io.vss_age==39);
    pcm.io.vss_changes=255;CHECK(pcm_vss_calculate(&pcm)==PCM_OK && pcm.io.vss_raw==65535);
    pcm.io.vss_age=1;CHECK(pcm_vss_calculate(&pcm)==PCM_OK && pcm.io.vss_raw==0);
    INIT();io.vss_gain=0;pcm.spark.vehicle_speed_high=0x12;pcm.io.vehicle_speed_fraction=0x34;pcm.io.vss_raw=0xffff;
    CHECK(pcm_vss_filter(&pcm)==PCM_OK && pcm.spark.vehicle_speed_high==0x12 && pcm.io.vehicle_speed_fraction==0x34);
    INIT();f.action=45;pcm.calibration=NULL;
    CHECK(pcm_ac_switch_inputs(&pcm)==PCM_BAD_CONFIGURATION && !f.masked && !pcm.runtime.diagnostic_switch && pcm.io.diagnostic_warm && f.used==2);
    INIT();root.mode_f=4;root.ac=NULL;f.fail_at=2;pcm.io.diagnostic_sample=0;
    CHECK(pcm_ac_switch_inputs(&pcm)==PCM_NO_HARDWARE && f.masked && pcm.runtime.diagnostic_switch);
    INIT();root.reference.mode_e=0;root.transmission=NULL;pcm.transmission.shift_lamp=true;
    CHECK(pcm_shift_lamp(&pcm)==PCM_OK && pcm.transmission.shift_lamp && f.used==0);
    root.reference.mode_e=4;pcm.runtime.diagnostic_switch=true;
    CHECK(pcm_shift_lamp(&pcm)==PCM_OK && pcm.transmission.shift_lamp && f.used==0);
    pcm.runtime.diagnostic_switch=false;f.action=44;f.memory[0x3fe0]=1;f.memory[0x3fe1]=0;
    CHECK(pcm_shift_lamp(&pcm)==PCM_BAD_CONFIGURATION && pcm.transmission.shift_counter==256 &&
          pcm.transmission.shift_delta==(uint16_t)(256-0xabcd) && word(f.memory,0x3fe0)==0x1234);
    INIT();environment.density.length=1;pcm.io.environmental_density=77;pcm.knock.burst_gain=88;
    CHECK(pcm_environment_inputs(&pcm)==PCM_BAD_CONFIGURATION && pcm.io.environmental_density==77 && pcm.knock.burst_gain==88);
#undef INIT
    puts("Six scheduled input groups, shared owners, delay expiry, quotient overflow and ordered failure prefixes pass.");
}

int main(int argc,char **argv)
{
    static Fixture f;Pcm pcm;PcmCalibration root;PcmSparkCalibration spark;
    PcmTransmissionCalibration transmission;PcmIacCalibration cal;PcmIoCalibration io;PcmAcCalibration ac;PcmEnvironmentCalibration environment;uint8_t patterns[256],baro[256],mat[256],ae[256],rpm[256],bias[8],density[12];
    if (argc==2 && strcmp(argv[1],"--contracts")==0) { input_contracts();return 0; }
    if (argc==2 && (strcmp(argv[1],"--input-defaults")==0 || strcmp(argv[1],"--input-backing")==0)) {
        input_init(&f,&pcm,&root,&spark,&transmission,patterns,&cal,&io,&ac,&environment);
        bool backing=strcmp(argv[1],"--input-backing")==0;printf("[");
        size_t count=backing?12:MAPSIZE(input_cal_addresses);
        for (size_t i=0;i<count;++i) {
            unsigned a=backing?0x4760+(unsigned)i:input_cal_addresses[i];
            printf("%s[%u,%u]",i?",":"",a,f.memory[a]);
        }
        puts("]");return 0;
    }
    if (argc==2) return inherited_io_fixture_main(argc,argv);
    unsigned mode,count;
    while (scanf("%u %u",&mode,&count)==2) {
        if (mode>14 || count>2048) return 2;
        input_init(&f,&pcm,&root,&spark,&transmission,patterns,&cal,&io,&ac,&environment);
        for (unsigned i=0;i<count;++i) { unsigned a,v;if (scanf("%u %u",&a,&v)!=2 || a>65535 || v>255) return 2;f.memory[a]=(uint8_t)v; }
        transfer(&pcm,f.memory,state_map,sizeof(state_map)/sizeof(state_map[0]),true);
        transfer(&pcm,f.memory,transmission_map,sizeof(transmission_map)/sizeof(transmission_map[0]),true);
        iac_state_transfer(&pcm,&f,true);transfer(&pcm,f.memory,slow_state_map,sizeof(slow_state_map)/sizeof(slow_state_map[0]),true);
        transfer(&pcm,f.memory,main_state_map,sizeof(main_state_map)/sizeof(main_state_map[0]),true);
        pcm.iac.step_control=f.memory[10];io_state_transfer(&pcm,&f,true);input_state_transfer(&pcm,&f,true);
        load_cal(&f,&root,&spark);memcpy(patterns,f.memory+0xb319,256);
        transfer(&cal,f.memory,iac_cal_map,sizeof(iac_cal_map)/sizeof(iac_cal_map[0]),true);
        transfer(&cal,f.memory,slow_cal_map,sizeof(slow_cal_map)/sizeof(slow_cal_map[0]),true);
        transfer(&cal,f.memory,main_cal_map,sizeof(main_cal_map)/sizeof(main_cal_map[0]),true);
        cal.step_battery_minimum=f.memory[0x4eb6];
        transfer(&io,f.memory,io_cal_map,sizeof(io_cal_map)/sizeof(io_cal_map[0]),true);
        memcpy(bias,f.memory+0x4e6b,8);io.map_bias.values=bias;io.map_bias.length=8;
#define LOAD_BACKING(a,c,v) memcpy(v,f.memory+(a),256);(c).values=(v);(c).length=256
        LOAD_BACKING(0x4ea6,cal.baro.curve,baro);LOAD_BACKING(0x4f17,cal.ac_temperature.curve,mat);
        LOAD_BACKING(0x50a3,cal.enrichment_curve,ae);LOAD_BACKING(0x5065,cal.follower_rpm,rpm);
#undef LOAD_BACKING
        root.reference.mode_e=f.memory[0x400e];
        transfer(&root,f.memory,input_knock_map,MAPSIZE(input_knock_map),true);
        transfer(&io,f.memory,input_io_map,MAPSIZE(input_io_map),true);
        transfer(&ac,f.memory,input_ac_map,MAPSIZE(input_ac_map),true);
        transfer(&environment,f.memory,input_environment_map,MAPSIZE(input_environment_map),true);
        transfer(&transmission,f.memory,input_transmission_map,MAPSIZE(input_transmission_map),true);
        memcpy(density,f.memory+0x4760,12);environment.density.values=density;environment.density.length=12;
        f.fail_at=f.memory[0x907];f.action=f.memory[0x908];f.masked=f.memory[0x909]!=0;
        PcmStatus status=PCM_OK;
#define RUN(call) do { status=(call);if (status!=PCM_OK) goto finished; } while (0)
        switch (mode) {
        case 0:RUN(pcm_map_transient(&pcm));break;
        case 1:RUN(pcm_vss_calculate(&pcm));break;
        case 2:RUN(pcm_vss_filter(&pcm));break;
        case 3:RUN(pcm_ac_switch_inputs(&pcm));break;
        case 4:RUN(pcm_shift_lamp(&pcm));break;
        case 5:RUN(pcm_environment_inputs(&pcm));break;
        case 6:RUN(pcm_map_transient(&pcm));RUN(pcm_map_input(&pcm));break;
        case 7:RUN(pcm_common_io(&pcm));RUN(pcm_vss_calculate(&pcm));RUN(pcm_vss_filter(&pcm));break;
        case 8:RUN(pcm_slot_06(&pcm));break;
        case 9:RUN(pcm_slot_07(&pcm));break;
        case 10:RUN(pcm_slot_09(&pcm));break;
        case 11:RUN(pcm_ac_switch_inputs(&pcm));RUN(pcm_map_transient(&pcm));RUN(pcm_map_input(&pcm));RUN(pcm_iac_background(&pcm));RUN(pcm_iac_control(&pcm));break;
        case 12:RUN(pcm_vss_calculate(&pcm));RUN(pcm_vss_filter(&pcm));RUN(pcm_iac_slow(&pcm));RUN(pcm_shift_lamp(&pcm));break;
        case 13:RUN(pcm_environment_inputs(&pcm));RUN(pcm_slot_07(&pcm));RUN(pcm_spark_control(&pcm));break;
        default:RUN(pcm_input_housekeeping(&pcm));RUN(pcm_ac_switch_inputs(&pcm));RUN(pcm_map_transient(&pcm));RUN(pcm_board_latch(&pcm));break;
        }
finished:
#undef RUN
        transfer(&pcm,f.memory,state_map,sizeof(state_map)/sizeof(state_map[0]),false);
        transfer(&pcm,f.memory,transmission_map,sizeof(transmission_map)/sizeof(transmission_map[0]),false);
        iac_state_transfer(&pcm,&f,false);transfer(&pcm,f.memory,slow_state_map,sizeof(slow_state_map)/sizeof(slow_state_map[0]),false);
        transfer(&pcm,f.memory,main_state_map,sizeof(main_state_map)/sizeof(main_state_map[0]),false);
        f.memory[10]=pcm.iac.step_control;io_state_transfer(&pcm,&f,false);input_state_transfer(&pcm,&f,false);
        CHECK(pcm.unresolved_task==PCM_TASK_COUNT);
        printf("{\"status\":%u,\"value\":0,\"state\":[",(unsigned)status);bool first=true;
        GROUP(command_outputs);GROUP(period_extra);GROUP(output_extra);GROUP(controller_extra);GROUP(transmission_outputs);GROUP(iac_outputs);GROUP(slow_outputs);GROUP(main_outputs);printf(",%u",f.memory[10]);GROUP(io_outputs);GROUP(input_outputs);
        printf("],\"masked\":%u,\"unresolved\":0,\"partial\":0,\"coordinates\":[0,0],\"events\":[",(unsigned)f.masked);
        for (unsigned i=0;i<f.used;++i) { Event *e=&f.events[i];printf("%s[\"%c\",%u,%u,%u,%u]",i?",":"",e->kind,e->width,e->address,e->value,(unsigned)e->masked); }
        puts("]}");
    }
    return 0;
}
