#define IAC_SLOW_FIXTURE_ENTRY inherited_slow_fixture_main
#include "iac_slow_test.c"
#include "iac_main_fixture_map.h"

static PcmStatus main_extension(Pcm *pcm,PcmTask task)
{
    Fixture *f=pcm->platform->context;CHECK(task==PCM_IAC_EXTENSION);
    PcmStatus result=record(f,'T',0,0x1803,f->action);
    if (result!=PCM_OK) return result;
    if (f->action==23) { pcm->runtime.engine_service=true;pcm->spark.service_flags=1;pcm->iac.service_value=93;pcm->iac.state_flags=0;pcm->iac.service_kicker=false;pcm->reference.latch_inhibited=false; }
    if (f->action==24) { pcm->scheduler.profiling_enabled=false;pcm->iac.transfer_flags|=0x40;pcm->reference.latch_inhibited=true;pcm->iac.state_flags=0; }
    return PCM_OK;
}
static void main_init(Fixture *f,Pcm *pcm,PcmCalibration *root,PcmSparkCalibration *spark,
                      PcmTransmissionCalibration *transmission,uint8_t *patterns,PcmIacCalibration *cal)
{
    slow_init(f,pcm,root,spark,transmission,patterns,cal);
    memcpy(f->memory+0x4ea6,main_baro_backing,256);
    memcpy(f->memory+0x4f17,main_ac_temperature_backing,256);
    memcpy(f->memory+0x50a3,main_enrichment_curve_backing,256);
    transfer(cal,f->memory,main_cal_map,sizeof(main_cal_map)/sizeof(main_cal_map[0]),false);
    memcpy(f->memory+0x4ea6,cal->baro.curve.values,cal->baro.curve.length);
    memcpy(f->memory+0x4f17,cal->ac_temperature.curve.values,cal->ac_temperature.curve.length);
    memcpy(f->memory+0x50a3,cal->enrichment_curve.values,cal->enrichment_curve.length);
    f->platform.task[PCM_IAC_EXTENSION]=main_extension;
    f->platform.task[PCM_IAC_CONTROL]=NULL;
}
static void main_contracts(void)
{
    static Fixture f;Pcm pcm;PcmCalibration root;PcmSparkCalibration spark;
    PcmTransmissionCalibration transmission;PcmIacCalibration cal;uint8_t patterns[256];
#define INIT() main_init(&f,&pcm,&root,&spark,&transmission,patterns,&cal)
    INIT();pcm.scheduler.profiling_enabled=true;f.platform.task[PCM_IAC_EXTENSION]=NULL;
    pcm.iac.transfer_flags=0x40;CHECK(pcm_iac_control(&pcm)==PCM_UNIMPLEMENTED && pcm.iac.transfer_flags==0x40 && pcm.unresolved_task==PCM_IAC_EXTENSION);
    INIT();pcm.scheduler.profiling_enabled=true;f.fail_at=1;pcm.iac.transfer_flags=0x40;
    CHECK(pcm_iac_control(&pcm)==PCM_NO_HARDWARE && pcm.iac.transfer_flags==0x40);
    INIT();pcm.calibration=NULL;pcm.iac.state_flags=1;pcm.iac.position=1;pcm.iac.target=99;pcm.iac.transfer_flags=0xff;
    CHECK(pcm_iac_control(&pcm)==PCM_OK && pcm.iac.target==0 && pcm.iac.transfer_flags==0xbf);
    INIT();pcm.calibration=NULL;pcm.runtime.engine_service=true;pcm.spark.service_flags=1;pcm.iac.service_value=87;
    CHECK(pcm_iac_control(&pcm)==PCM_OK && pcm.iac.target==87 && !(pcm.iac.context&0x0c));
    INIT();pcm.runtime.engine_service=true;pcm.spark.service_flags=3;pcm.iac.service_value=87;pcm.runtime.spark_running=true;
    CHECK(pcm_iac_control(&pcm)==PCM_OK && pcm.spark.iac_desired_speed==87 && (pcm.iac.transfer_flags&0x40));
    CHECK(pcm_iac_background(&pcm)==PCM_OK && pcm.spark.iac_desired_speed==87);
    INIT();pcm.iac.service_kicker=true;pcm.iac.service_kicker_value=true;pcm.iac.kicker_timer=91;pcm.iac.tps_zero_high=123;pcm.runtime.engine_service=true;
    CHECK(pcm_iac_control(&pcm)==PCM_OK && (pcm.iac.kicker_flags&4) && !pcm.iac.kicker_request && pcm.iac.kicker_timer==91 && pcm.iac.tps_zero_high==123);
    INIT();pcm.iac.state_flags=1;pcm.iac.position=0;pcm.reference.latch_inhibited=true;
    pcm.iac.bank[0].no_ac=0x12ab;pcm.iac.bank[0].ac=0x34cd;
    CHECK(pcm_iac_control(&pcm)==PCM_OK && pcm.iac.state_flags==4 && pcm.iac.target==cal.park_target);
    CHECK((pcm.iac.bank[0].no_ac&255)==0xab && (pcm.iac.bank[0].ac&255)==0xcd);
    INIT();pcm.iac.derivative_filtered=0x1234;pcm.iac.rpm_error_filtered=0x5678;pcm.spark.override_request=true;
    CHECK(pcm_iac_start(&pcm)==PCM_OK && pcm.iac.derivative_filtered==0x8034 && (pcm.iac.rpm_error_filtered&255)==0x78 && !pcm.spark.override_request);
    INIT();pcm.iac.context=8;pcm.iac.rpm_error=255;pcm.iac.proportional=1;
    CHECK(pcm_iac_proportional(&pcm)==PCM_OK);
    INIT();pcm.iac.pre_baro_flow=99;pcm.iac.airflow=77;pcm.iac.target=55;cal.baro.curve.length=1;
    CHECK(pcm_iac_convert(&pcm,123)==PCM_BAD_CONFIGURATION && pcm.iac.pre_baro_flow==123 && pcm.iac.airflow==77 && pcm.iac.target==55);
    INIT();cal.options=0x40;cal.ac_temperature.curve.length=1;pcm.iac.context=0;
    pcm.iac.gear_status=0;pcm.iac.ac_request=true;pcm.iac.ac_adder=77;pcm.iac.transfer_flags=0x0f;
    CHECK(pcm_iac_context(&pcm)==PCM_BAD_CONFIGURATION && (pcm.iac.context&3)==3);
    CHECK(pcm.iac.ac_adder==77 && pcm.iac.ac_divider==cal.ac_decay_reload && pcm.iac.transfer_flags==0x0f);
    INIT();cal.enrichment_curve.length=1;cal.enrichment_flow=0;cal.enrichment_throttle=255;
    pcm.iac.selected_integral=0x1000;pcm.iac.composite_flow=0;pcm.iac.enrichment=77;pcm.iac.pre_baro_flow=33;
    CHECK(pcm_iac_compose(&pcm)==PCM_BAD_CONFIGURATION && pcm.iac.composite_flow==0x1000);
    CHECK(pcm.iac.enrichment==77 && pcm.iac.pre_baro_flow==33);
    INIT();pcm.iac.context=0x84;pcm.iac.qualification_delay=1;cal.closed_throttle=255;cal.closed_speed=255;
    pcm.iac.selected_integral=7;pcm.iac.bank[0].no_ac=0x1234;pcm.iac.rpm_error=255;
    CHECK(pcm_iac_integral(&pcm)==PCM_OK && pcm.iac.qualification_delay==0 && !(pcm.iac.context&8));
    CHECK(pcm.iac.bank[0].no_ac==0x1234 && pcm.iac.selected_integral==0x1234);
    INIT();pcm.iac.context=4;pcm.iac.bank[0].no_ac=0xffff;pcm.iac.position=0;
    pcm.reference.coolant=255;cal.reconcile_coolant=0;cal.reconcile_flow[0]=0;cal.reconcile_phase=255;
    cal.closed_throttle=255;cal.closed_speed=255;pcm.iac.rpm_error=255;pcm.iac.state_flags=4;
    CHECK(pcm_iac_integral(&pcm)==PCM_OK && pcm.iac.position==255 && !(pcm.iac.state_flags&4));
    CHECK(pcm.iac.bank[0].no_ac==0xffff && f.used==0);
    INIT();cal.options=0;cal.baro.offset=0;cal.baro.limit=0;cal.baro.curve.scale=0;
    uint8_t knots[]={128,128};cal.baro.curve.values=knots;cal.baro.curve.length=2;
    for (unsigned i=0;i<18;++i) cal.position_curve[i]=(uint8_t)(255-11*i);
    CHECK(pcm_iac_convert(&pcm,0xffff)==PCM_OK && pcm.iac.target==cal.position_curve[16]);
    bool exited;CHECK(pcm_iac_service(&pcm,NULL)==PCM_BAD_CONFIGURATION);
    pcm.reference.latch_inhibited=true;CHECK(pcm_iac_service(&pcm,&exited)==PCM_OK && !exited);
    PcmOffsetCurve curve={10,20,{2,0,knots}};uint8_t result=77;
    CHECK(pcm_lookup_offset(0,&curve,&result)==PCM_OK && result==128);
    CHECK(pcm_lookup_offset(0,NULL,&result)==PCM_BAD_CONFIGURATION);
#undef INIT
    puts("Main IAC service escapes, reset/seed fractions, startup byte stores, missing module and checked conversion prefixes pass.");
}
int main(int argc,char **argv)
{
    static Fixture f;Pcm pcm;PcmCalibration root;PcmSparkCalibration spark;
    PcmTransmissionCalibration transmission;PcmIacCalibration cal;uint8_t patterns[256],baro[256],mat[256],ae[256],rpm[256];
    if (argc==2 && strcmp(argv[1],"--contracts")==0) { main_contracts();return 0; }
    if (argc==2 && strcmp(argv[1],"--iac-main-defaults")==0) {
        main_init(&f,&pcm,&root,&spark,&transmission,patterns,&cal);printf("[");bool first=true;
        for (size_t i=0;i<sizeof(main_cal_map)/sizeof(main_cal_map[0]);++i) {
            const Mapping *m=&main_cal_map[i];const uint8_t *p=(const uint8_t *)&cal+m->offset;
            uint16_t word_value=0;if (m->width==16) memcpy(&word_value,p,sizeof(word_value));
            for (unsigned j=0;j<m->count*(m->width/8u);++j) {
                unsigned value=m->width==16?(j?word_value&255u:word_value>>8):p[j];
                printf("%s[%u,%u]",first?"":",",m->address+j,value);first=false;
            }
        }
#define DEFAULT_KNOTS(a,c) for (unsigned i=0;i<(c).length;++i) printf(",[%u,%u]",(a)+i,(c).values[i])
        DEFAULT_KNOTS(0x4ea6,cal.baro.curve);DEFAULT_KNOTS(0x4f17,cal.ac_temperature.curve);DEFAULT_KNOTS(0x50a3,cal.enrichment_curve);
#undef DEFAULT_KNOTS
        puts("]");return 0;
    }
    if (argc==2 && strcmp(argv[1],"--main-backing")==0) {
        printf("[");for (unsigned i=0;i<256;++i) printf("%s[%u,%u],[%u,%u],[%u,%u]",i?",":"",0x4ea6+i,main_baro_backing[i],0x4f17+i,main_ac_temperature_backing[i],0x50a3+i,main_enrichment_curve_backing[i]);puts("]");return 0;
    }
    if (argc==2) return inherited_slow_fixture_main(argc,argv);
    unsigned mode,count;
    while (scanf("%u %u",&mode,&count)==2) {
        if (mode>16 || count>2048) return 2;
        main_init(&f,&pcm,&root,&spark,&transmission,patterns,&cal);
        for (unsigned i=0;i<count;++i) { unsigned a,v;if (scanf("%u %u",&a,&v)!=2 || a>65535 || v>255) return 2;f.memory[a]=(uint8_t)v; }
        transfer(&pcm,f.memory,state_map,sizeof(state_map)/sizeof(state_map[0]),true);
        transfer(&pcm,f.memory,transmission_map,sizeof(transmission_map)/sizeof(transmission_map[0]),true);
        iac_state_transfer(&pcm,&f,true);transfer(&pcm,f.memory,slow_state_map,sizeof(slow_state_map)/sizeof(slow_state_map[0]),true);
        transfer(&pcm,f.memory,main_state_map,sizeof(main_state_map)/sizeof(main_state_map[0]),true);
        load_cal(&f,&root,&spark);memcpy(patterns,f.memory+0xb319,256);
        transfer(&cal,f.memory,iac_cal_map,sizeof(iac_cal_map)/sizeof(iac_cal_map[0]),true);
        transfer(&cal,f.memory,slow_cal_map,sizeof(slow_cal_map)/sizeof(slow_cal_map[0]),true);
        transfer(&cal,f.memory,main_cal_map,sizeof(main_cal_map)/sizeof(main_cal_map[0]),true);
#define LOAD_BACKING(a,c,v) memcpy(v,f.memory+(a),256);(c).values=(v);(c).length=256
        LOAD_BACKING(0x4ea6,cal.baro.curve,baro);LOAD_BACKING(0x4f17,cal.ac_temperature.curve,mat);
        LOAD_BACKING(0x50a3,cal.enrichment_curve,ae);LOAD_BACKING(0x5065,cal.follower_rpm,rpm);
#undef LOAD_BACKING
        f.fail_at=f.memory[0x907];f.action=f.memory[0x908];f.masked=f.memory[0x909]!=0;
        if (f.memory[0x90f]&4) f.platform.task[PCM_IAC_EXTENSION]=NULL;
        PcmStatus status;bool exited=false;uint8_t value=0;
        switch (mode) {
        case 0:status=pcm_iac_control(&pcm);break;
        case 1:status=pcm_iac_seed_cells(&pcm);break;
        case 2:status=pcm_iac_start(&pcm);break;
        case 3:status=pcm_iac_context(&pcm);break;
        case 4:status=pcm_iac_error(&pcm);break;
        case 5:status=pcm_iac_integral(&pcm);break;
        case 6:status=pcm_iac_proportional(&pcm);break;
        case 7:status=pcm_iac_derivative(&pcm);break;
        case 8:status=pcm_iac_compose(&pcm);break;
        case 9:status=pcm_iac_convert(&pcm,word(f.memory,0x900));break;
        case 10:status=pcm_iac_service(&pcm,&exited);value=exited;break;
        case 11:status=pcm_lookup_offset(f.memory[0x900],&cal.baro,&value);break;
        case 12:status=pcm_iac_control(&pcm);if (status==PCM_OK) { pcm.scheduler.phase=7;status=pcm_iac_background(&pcm); }break;
        case 13:status=pcm_iac_background(&pcm);if (status==PCM_OK) { pcm.scheduler.phase=3;status=pcm_iac_control(&pcm); }break;
        case 14:status=pcm_iac_slow(&pcm);if (status==PCM_OK) { pcm.scheduler.phase=3;status=pcm_iac_control(&pcm); }break;
        case 15:status=pcm_iac_control(&pcm);if (status==PCM_OK) { pcm.scheduler.phase=9;status=pcm_iac_slow(&pcm); }break;
        default:status=pcm_iac_control(&pcm);if (status==PCM_OK) { pcm.scheduler.phase=8;status=pcm_spark_control(&pcm); }break;
        }
        transfer(&pcm,f.memory,state_map,sizeof(state_map)/sizeof(state_map[0]),false);
        transfer(&pcm,f.memory,transmission_map,sizeof(transmission_map)/sizeof(transmission_map[0]),false);
        iac_state_transfer(&pcm,&f,false);transfer(&pcm,f.memory,slow_state_map,sizeof(slow_state_map)/sizeof(slow_state_map[0]),false);
        transfer(&pcm,f.memory,main_state_map,sizeof(main_state_map)/sizeof(main_state_map[0]),false);
        unsigned unresolved=pcm.unresolved_task==PCM_IAC_EXTENSION?9:0;
        CHECK(pcm.unresolved_task==PCM_TASK_COUNT || unresolved!=0);
        printf("{\"status\":%u,\"value\":%u,\"state\":[",(unsigned)status,value);bool first=true;
        GROUP(command_outputs);GROUP(period_extra);GROUP(output_extra);GROUP(controller_extra);GROUP(transmission_outputs);GROUP(iac_outputs);GROUP(slow_outputs);GROUP(main_outputs);
        printf("],\"masked\":%u,\"unresolved\":%u,\"partial\":0,\"coordinates\":[0,0],\"events\":[",(unsigned)f.masked,unresolved);
        for (unsigned i=0;i<f.used;++i) { Event *e=&f.events[i];printf("%s[\"%c\",%u,%u,%u,%u]",i?",":"",e->kind,e->width,e->address,e->value,(unsigned)e->masked); }
        puts("]}");
    }
    return 0;
}
