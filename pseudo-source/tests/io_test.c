#define IAC_STEP_FIXTURE_ENTRY inherited_step_fixture_main
#include "iac_step_test.c"
#include "board_io.h"
#include "io_fixture_map.h"

static void io_state_transfer(Pcm *pcm,Fixture *f,bool load)
{
    for (size_t i=0;i<sizeof(io_state_map)/sizeof(io_state_map[0]);++i) {
        const Mapping *m=&io_state_map[i];
        if (m->width==7) {
            if (load) pcm->io.output_context=f->memory[0x4b]&0x6f;
            else f->memory[0x4b]=(uint8_t)((f->memory[0x4b]&0x90)|(pcm->io.output_context&0x6f));
        } else if (m->width==15) {
            if (load) pcm->io.status_context=word(f->memory,0x73)&0xbfff;
            else { uint16_t value=(uint16_t)((word(f->memory,0x73)&0x4000)|(pcm->io.status_context&0xbfff));f->memory[0x73]=(uint8_t)(value>>8);f->memory[0x74]=(uint8_t)value; }
        } else transfer(pcm,f->memory,m,1,load);
    }
}
static void io_effect(Fixture *f,unsigned action,uint16_t address)
{
    Pcm *pcm=f->pcm;
    if (action==28 && address==0x3060) { pcm->spark.output_request=true;pcm->iac.kicker_request=false; }
    if (action==29 && address==0x3060) { pcm->spark.output_request=false;pcm->iac.kicker_request=true;pcm->io.output_context=0x6f;pcm->transmission.output_shadow=0xcd;pcm->io.auxiliary_output=0x89; }
    if (action==30 && address==0x3062) { pcm->iac.input_shadow=0xdd;f->memory[0x3064]=0x26;pcm->io.auxiliary_output=0xef; }
    if (action==31 && address==0x3064) { pcm->iac.input_shadow=0x55;pcm->io.auxiliary_output=0x5a; }
    if (action==32 && address==0x3067) pcm->iac.input_shadow=0x10;
    if (action==33 && address==0x3ffc) { f->memory[0x3ffc]=0x12;f->memory[0x3ffd]=0x34;pcm->runtime.service_output_mirror=true; }
    if (action==35 && address==0x3ffc) { pcm->transmission.output_shadow=0x6a;pcm->spark.output_request=true;pcm->iac.kicker_request=true; }
    if (action==36 && address==0x3ffa) { pcm->reference.extra_request=true;pcm->io.status_context=0xabcd; }
    if (action==38 && address==0x3fc4) pcm->io.vss_timestamp=word(f->memory,0x3fc4);
    if (action==39 && address==0x3fc4) { pcm->io.vss_timestamp=(uint16_t)(word(f->memory,0x3fc4)^0x8000);pcm->io.vss_changes=255; }
    if ((action==40 || action==41) && address==PCM_COPRST) {
        PcmCalibration *root=(PcmCalibration *)(void *)pcm->calibration;
        root->mode_f=action==40?0:0x44;pcm->iac.input_shadow=0x15;
    }
}
static PcmStatus io_read8(void *context,uint16_t address,uint8_t *value)
{
    if (address!=0x3060 && address!=0x3064) return iac_read8(context,address,value);
    Fixture *f=context;uint8_t sample=f->memory[address];PcmStatus result=record(f,'R',8,address,sample);
    if (result==PCM_OK) { *value=sample;if (f->action==28 || f->action==31) io_effect(f,f->action,address); }
    return result;
}
static PcmStatus io_write8(void *context,uint16_t address,uint8_t value)
{
    if (address!=0x3060 && address!=0x3062 && address!=0x3067 && address!=PCM_COPRST) return write8(context,address,value);
    Fixture *f=context;PcmStatus result=record(f,'W',8,address,value);
    if (result==PCM_OK) { f->memory[address]=value;if (f->action==29 || f->action==30 || f->action==32 || f->action==40 || f->action==41) io_effect(f,f->action,address); }
    return result;
}
static PcmStatus io_read16(void *context,uint16_t address,uint16_t *value)
{
    if (address!=0x3ffc && address!=0x3ffa && address!=0x3fc4) return slot_read16(context,address,value);
    Fixture *f=context;uint16_t sample=word(f->memory,address);PcmStatus result=record(f,'R',16,address,sample);
    if (result==PCM_OK) { *value=sample;if (f->action==33 || f->action==36 || f->action==38 || f->action==39) io_effect(f,f->action,address); }
    return result;
}
static PcmStatus io_write16(void *context,uint16_t address,uint16_t value)
{
    if (address!=0x3ffc) return slot_write16(context,address,value);
    Fixture *f=context;PcmStatus result=record(f,'W',16,address,value);
    if (result==PCM_OK) { f->memory[address]=(uint8_t)(value>>8);f->memory[address+1]=(uint8_t)value;if (f->action==35) io_effect(f,35,address); }
    return result;
}
static PcmStatus io_delay(void *context,uint16_t cycles)
{
    Fixture *f=context;CHECK(cycles==11);PcmStatus result=record(f,'D',0,0,cycles);
    if (result==PCM_OK && f->action==34) { f->memory[0x3ffc]=0x12;f->memory[0x3ffd]=0x34;f->pcm->runtime.service_output_mirror=true; }
    return result;
}
static PcmStatus io_mask(void *context,bool masked)
{
    Fixture *f=context;PcmStatus result=mask(context,masked);
    if (result==PCM_OK && !masked && f->action==37) {
        f->pcm->reference.extra_request=false;f->pcm->io.status_context=0x0200;
        f->pcm->io.vss_timestamp=0xfffe;f->pcm->io.vss_changes=255;f->pcm->iac.input_shadow=0xff;
    }
    if (result==PCM_OK && !masked && f->action==43 && f->pcm->reference.extra_request) {
        f->memory[0x3ffa]=0;f->memory[0x3ffb]=0;
    }
    return result;
}
static void io_init(Fixture *f,Pcm *pcm,PcmCalibration *root,PcmSparkCalibration *spark,
                    PcmTransmissionCalibration *transmission,uint8_t *patterns,PcmIacCalibration *iac,PcmIoCalibration *io)
{
    step_init(f,pcm,root,spark,transmission,patterns,iac);*io=pcm_reference_io_calibration;root->io=io;
    transfer(io,f->memory,io_cal_map,sizeof(io_cal_map)/sizeof(io_cal_map[0]),false);
    memcpy(f->memory+0x4e6b,io_bias_backing,8);
    f->platform.read8=io_read8;f->platform.write8=io_write8;f->platform.read16=io_read16;f->platform.write16=io_write16;
    f->platform.delay_cycles=io_delay;f->platform.mask_irq=io_mask;
    f->platform.task[PCM_COMMON_IO]=f->platform.task[PCM_INPUT_HOUSEKEEPING]=NULL;
}

static void io_contracts(void)
{
    static Fixture f;Pcm pcm;PcmCalibration root;PcmSparkCalibration spark;
    PcmTransmissionCalibration transmission;PcmIacCalibration iac;PcmIoCalibration io;uint8_t patterns[256];
#define INIT() io_init(&f,&pcm,&root,&spark,&transmission,patterns,&iac,&io)
    INIT();f.memory[0x3ffc]=0xab;f.memory[0x3ffd]=0xcf;f.memory[0x3060]=0xff;f.memory[0x3064]=0x15;
    pcm.runtime.service_output_mirror=true;pcm.spark.output_request=true;pcm.transmission.output_shadow=0x9c;pcm.io.auxiliary_output=0x66;
    CHECK(pcm_board_latch(&pcm)==PCM_OK && f.used==10 && !f.masked);
    CHECK(word(f.memory,0x3ffc)==0xabc7 && f.memory[0x3060]==0x10 && pcm.io.output_context==0x6f);
    CHECK(f.memory[0x3062]==0x9c && pcm.iac.input_shadow==0x15 && f.memory[0x3067]==0x66);
    CHECK(f.events[1].kind=='R' && f.events[1].width==16 && f.events[2].kind=='D' && f.events[2].value==11);
    INIT();pcm.calibration=NULL;CHECK(pcm_board_latch(&pcm)==PCM_OK);
    INIT();f.platform.delay_cycles=NULL;f.memory[0x3ffc]=0x12;f.memory[0x3ffd]=0x34;
    CHECK(pcm_board_latch(&pcm)==PCM_NO_HARDWARE && f.masked && f.used==2 && word(f.memory,0x3ffc)==0x1234);
    INIT();f.action=29;f.memory[0x3060]=0x65;pcm.spark.output_request=true;pcm.iac.kicker_request=false;
    CHECK(pcm_board_ports(&pcm)==PCM_OK && f.memory[0x3060]==0x10 && pcm.spark.output_request && !pcm.iac.kicker_request);
    CHECK(pcm.io.output_context==0x65 && f.memory[0x3062]==0xcd && f.memory[0x3067]==0x89);
    INIT();f.action=34;f.memory[0x3ffc]=0xab;f.memory[0x3ffd]=0xcf;
    CHECK(pcm_board_latch(&pcm)==PCM_OK && word(f.memory,0x3ffc)==0xabc7);
    INIT();f.action=37;f.memory[0x3ffa]=4;f.memory[0x3ffb]=0;f.memory[0x3fc4]=0;f.memory[0x3fc5]=1;
    CHECK(pcm_vss_sample(&pcm)==PCM_OK && pcm.io.status_context==0x200 && !pcm.reference.extra_request);
    CHECK(pcm.io.vss_changes==0 && pcm.io.vss_timestamp==1 && f.used==4);
    INIT();f.memory[0x3ffa]=0x40;pcm.reference.extra_request=false;pcm.io.vss_changes=7;
    CHECK(pcm_vss_sample(&pcm)==PCM_OK && pcm.reference.extra_request && pcm.io.status_context==0 && f.used==3 && pcm.io.vss_changes==7);
    INIT();pcm.io.brake_active=true;pcm.iac.input_shadow=0;pcm.io.brake_count=77;pcm.calibration=NULL;
    CHECK(pcm_brake_filter(&pcm)==PCM_OK && pcm.io.brake_count==0);
    pcm.iac.input_shadow=2;CHECK(pcm_brake_filter(&pcm)==PCM_BAD_CONFIGURATION);
    INIT();io.brake_delay=1;pcm.io.brake_count=0;pcm.iac.input_shadow=0;
    CHECK(pcm_brake_filter(&pcm)==PCM_OK && pcm.io.brake_count==1 && !pcm.io.brake_active);
    CHECK(pcm_brake_filter(&pcm)==PCM_OK && pcm.io.brake_count==1 && pcm.io.brake_active);
    INIT();pcm.reference.map_sample=255;pcm.io.map_filter=0xffff;io.map_normal_gain=0;
    CHECK(pcm_map_input(&pcm)==PCM_OK && pcm.io.map_filter==0xffff && pcm.spark.map_filtered==0);
    INIT();pcm.spark.load_status=0x48;pcm.runtime.fuel_running=true;io.map_throttle_gain=0;
    pcm.reference.rpm_coordinate=255;io.map_bias.limit=255;io.map_bias.length=1;pcm.io.map_filter=0x1234;pcm.spark.map_filtered=77;
    CHECK(pcm_map_input(&pcm)==PCM_BAD_CONFIGURATION && pcm.io.map_filter==0x1234 && pcm.spark.map_filtered==77);
    pcm.spark.load_status=0;CHECK(pcm_map_input(&pcm)==PCM_OK);
    INIT();pcm.calibration=NULL;CHECK(pcm_input_housekeeping(&pcm)==PCM_BAD_CONFIGURATION && f.used==1 && f.events[0].value==0xaa);
    INIT();f.action=40;root.mode_f=0x44;
    CHECK(pcm_input_housekeeping(&pcm)==PCM_OK && pcm.iac.ac_request && pcm.io.ac_mirror && pcm.iac.park_neutral && f.used==1);
    INIT();root.mode_f=4;pcm.iac.ac_request=true;pcm.io.ac_mirror=false;pcm.iac.input_shadow=0;
    CHECK(pcm_input_housekeeping(&pcm)==PCM_OK && pcm.iac.ac_request && !pcm.io.ac_mirror);
    INIT();root.io=NULL;pcm.io.map_filter=0x1234;
    CHECK(pcm_common_io(&pcm)==PCM_BAD_CONFIGURATION && f.used==10 && !f.masked && pcm.io.map_filter==0x1234);
#undef INIT
    puts("Board word/byte order,11-cycle delay, split owners, capped-before-offset MAP, VSS latch/REF flag and input COP prefix pass.");
}

int main(int argc,char **argv)
{
    static Fixture f;Pcm pcm;PcmCalibration root;PcmSparkCalibration spark;
    PcmTransmissionCalibration transmission;PcmIacCalibration cal;PcmIoCalibration io;uint8_t patterns[256],baro[256],mat[256],ae[256],rpm[256],bias[8];
    if (argc==2 && strcmp(argv[1],"--contracts")==0) { io_contracts();return 0; }
    if (argc==2 && strcmp(argv[1],"--io-defaults")==0) {
        io=pcm_reference_io_calibration;printf("[");bool first=true;
        for (size_t i=0;i<sizeof(io_cal_map)/sizeof(io_cal_map[0]);++i) {
            const Mapping *m=&io_cal_map[i];const uint8_t *p=(const uint8_t *)&io+m->offset;
            printf("%s[%u,%u]",first?"":",",m->address,*p);first=false;
        }
        for (unsigned i=0;i<io.map_bias.length;++i) printf(",[%u,%u]",0x4e6b+i,io.map_bias.values[i]);
        puts("]");return 0;
    }
    if (argc==2 && strcmp(argv[1],"--io-backing")==0) {
        printf("[");for (unsigned i=0;i<8;++i) printf("%s[%u,%u]",i?",":"",0x4e6b+i,io_bias_backing[i]);puts("]");return 0;
    }
    if (argc==2) return inherited_step_fixture_main(argc,argv);
    unsigned mode,count;
    while (scanf("%u %u",&mode,&count)==2) {
        if (mode>12 || count>2048) return 2;
        io_init(&f,&pcm,&root,&spark,&transmission,patterns,&cal,&io);
        for (unsigned i=0;i<count;++i) { unsigned a,v;if (scanf("%u %u",&a,&v)!=2 || a>65535 || v>255) return 2;f.memory[a]=(uint8_t)v; }
        transfer(&pcm,f.memory,state_map,sizeof(state_map)/sizeof(state_map[0]),true);
        transfer(&pcm,f.memory,transmission_map,sizeof(transmission_map)/sizeof(transmission_map[0]),true);
        iac_state_transfer(&pcm,&f,true);transfer(&pcm,f.memory,slow_state_map,sizeof(slow_state_map)/sizeof(slow_state_map[0]),true);
        transfer(&pcm,f.memory,main_state_map,sizeof(main_state_map)/sizeof(main_state_map[0]),true);
        pcm.iac.step_control=f.memory[10];io_state_transfer(&pcm,&f,true);
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
        f.fail_at=f.memory[0x907];f.action=f.memory[0x908];f.masked=f.memory[0x909]!=0;
        PcmStatus status=PCM_OK;
#define RUN(call) do { status=(call);if (status!=PCM_OK) goto finished; } while (0)
        switch (mode) {
        case 0:RUN(pcm_board_latch(&pcm));break;
        case 1:RUN(pcm_board_ports(&pcm));break;
        case 2:RUN(pcm_map_input(&pcm));break;
        case 3:RUN(pcm_vss_sample(&pcm));break;
        case 4:RUN(pcm_brake_filter(&pcm));break;
        case 5:RUN(pcm_input_housekeeping(&pcm));break;
        case 6:RUN(pcm_common_io(&pcm));break;
        case 7:RUN(pcm_common_io(&pcm));RUN(pcm_input_housekeeping(&pcm));break;
        case 8:RUN(pcm_iac_step(&pcm));RUN(pcm_common_io(&pcm));RUN(pcm_input_housekeeping(&pcm));RUN(pcm_iac_control(&pcm));break;
        case 9:RUN(pcm_common_io(&pcm));RUN(pcm_reference_common(&pcm));break;
        case 10:RUN(pcm_input_housekeeping(&pcm));RUN(pcm_iac_control(&pcm));break;
        case 11:RUN(pcm_board_latch(&pcm));RUN(pcm_input_housekeeping(&pcm));RUN(pcm_iac_background(&pcm));break;
        default:RUN(pcm_common_io(&pcm));RUN(pcm_transmission_outputs(&pcm));RUN(pcm_iac_step(&pcm));break;
        }
finished:
#undef RUN
        transfer(&pcm,f.memory,state_map,sizeof(state_map)/sizeof(state_map[0]),false);
        transfer(&pcm,f.memory,transmission_map,sizeof(transmission_map)/sizeof(transmission_map[0]),false);
        iac_state_transfer(&pcm,&f,false);transfer(&pcm,f.memory,slow_state_map,sizeof(slow_state_map)/sizeof(slow_state_map[0]),false);
        transfer(&pcm,f.memory,main_state_map,sizeof(main_state_map)/sizeof(main_state_map[0]),false);
        f.memory[10]=pcm.iac.step_control;io_state_transfer(&pcm,&f,false);
        CHECK(pcm.unresolved_task==PCM_TASK_COUNT);
        printf("{\"status\":%u,\"value\":0,\"state\":[",(unsigned)status);bool first=true;
        GROUP(command_outputs);GROUP(period_extra);GROUP(output_extra);GROUP(controller_extra);GROUP(transmission_outputs);GROUP(iac_outputs);GROUP(slow_outputs);GROUP(main_outputs);printf(",%u",f.memory[10]);GROUP(io_outputs);
        printf("],\"masked\":%u,\"unresolved\":0,\"partial\":0,\"coordinates\":[0,0],\"events\":[",(unsigned)f.masked);
        for (unsigned i=0;i<f.used;++i) { Event *e=&f.events[i];printf("%s[\"%c\",%u,%u,%u,%u]",i?",":"",e->kind,e->width,e->address,e->value,(unsigned)e->masked); }
        puts("]}");
    }
    return 0;
}
