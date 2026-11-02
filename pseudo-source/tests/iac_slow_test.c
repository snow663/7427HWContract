#define IAC_FIXTURE_ENTRY inherited_iac_fixture_main
#include "iac_test.c"
#include "iac_slow_fixture_map.h"

static PcmStatus slow_task(Pcm *pcm,PcmTask task)
{
    Fixture *f=pcm->platform->context;
    uint16_t address=task==PCM_EGR_DEMAND?0xcf16:0xd4da;
    PcmStatus result=record(f,'T',0,address,f->action);
    if (result!=PCM_OK) return result;
    if (task==PCM_EGR_DEMAND && f->action==20) { pcm->runtime.spark_running=false;pcm->iac.target=77; }
    if (task==PCM_EGR_DEMAND && f->action==21) {
        pcm->runtime.spark_running=true;pcm->iac.context=3;pcm->reference.throttle=24;
        pcm->spark.vehicle_speed_high=190;pcm->scheduler.phase=0x29;pcm->iac.bank[1].ac_snapshot=100;
    }
    if (task==PCM_VSS_FILTER && f->action==22) {
        pcm->iac.follower_filtered=0xabcd;pcm->spark.vehicle_speed_high=1;pcm->scheduler.phase=9;
    }
    return PCM_OK;
}
static void slow_init(Fixture *f,Pcm *pcm,PcmCalibration *root,PcmSparkCalibration *spark,
                      PcmTransmissionCalibration *transmission,uint8_t *patterns,PcmIacCalibration *cal)
{
    iac_init(f,pcm,root,spark,transmission,patterns,cal);
    f->platform.task[PCM_SLOT_09]=NULL;
    f->platform.task[PCM_EGR_DEMAND]=f->platform.task[PCM_VSS_FILTER]=slow_task;
    memcpy(f->memory+0x5065,slow_rpm_backing,256);
    transfer(cal,f->memory,slow_cal_map,sizeof(slow_cal_map)/sizeof(slow_cal_map[0]),false);
    memcpy(f->memory+0x5065,cal->follower_rpm.values,cal->follower_rpm.length);
}
static void slow_contracts(void)
{
    static Fixture f;Pcm pcm;PcmCalibration root;PcmSparkCalibration spark;
    PcmTransmissionCalibration transmission;PcmIacCalibration cal;uint8_t patterns[256];
#define INIT() slow_init(&f,&pcm,&root,&spark,&transmission,patterns,&cal)
    INIT();pcm.calibration=NULL;pcm.iac.follower=123;pcm.iac.startup_rpm_hold=7;
    CHECK(pcm_iac_slow(&pcm)==PCM_OK && pcm.iac.follower==123 && pcm.iac.startup_rpm_hold==7);
    CHECK(pcm_slot_09(&pcm)==PCM_OK && f.used==2 && f.events[0].address==0xcf16 && f.events[1].address==0xd4da);
    pcm.runtime.spark_running=true;CHECK(pcm_iac_slow(&pcm)==PCM_BAD_CONFIGURATION);
    INIT();pcm.iac.context=0xdf;pcm.spark.override_request=true;pcm.iac.target=33;pcm.calibration=NULL;
    CHECK(pcm_iac_reset_request(&pcm)==PCM_OK && pcm.iac.target==0 && pcm.iac.position==255);
    CHECK(pcm.iac.context==0xc3 && pcm.spark.override_request && pcm.iac.state_flags==1);
    INIT();pcm.reference.latch_inhibited=true;pcm.calibration=NULL;
    CHECK(pcm_iac_reset_admit(&pcm)==PCM_OK && pcm.iac.position==255);
    INIT();pcm.runtime.ignition_off=true;pcm.iac.target=33;pcm.spark.vehicle_speed_high=0;
    CHECK(pcm_iac_reset_admit(&pcm)==PCM_OK && pcm.iac.target==33);
    pcm.spark.vehicle_speed_high=cal.reset_speed;CHECK(pcm_iac_reset_admit(&pcm)==PCM_OK && pcm.iac.position==255);
    INIT();pcm.iac.startup_rpm_adder=2;pcm.iac.startup_rpm_hold=1;pcm.scheduler.phase=9;
    CHECK(pcm_iac_slow_decays(&pcm)==PCM_OK && pcm.iac.startup_rpm_hold==0 && pcm.iac.startup_rpm_adder==2);
    CHECK(pcm_iac_slow_decays(&pcm)==PCM_OK && pcm.iac.startup_rpm_adder==1);
    pcm.iac.startup_cancel=true;pcm.iac.startup_flow=7;pcm.iac.startup_flow_divider=123;
    CHECK(pcm_iac_slow_decays(&pcm)==PCM_OK && pcm.iac.startup_flow==0 && pcm.iac.startup_flow_divider==123 && pcm.iac.startup_rpm_adder==0);
    INIT();pcm.iac.context=2;pcm.iac.bank[1].no_ac=0xff81;pcm.iac.bank[1].no_ac_snapshot=250;cal.drive_snapshot_delta[0]=10;
    CHECK(pcm_iac_drive_limit(&pcm)==PCM_OK && pcm.iac.bank[1].no_ac==0xff81);
    pcm.iac.bank[1].no_ac_snapshot=2;CHECK(pcm_iac_drive_limit(&pcm)==PCM_OK && pcm.iac.bank[1].no_ac==0x0c00);
    INIT();cal.fault_options=4;cal.options=4;cal.kicker_baseline_limit=1;
    pcm.iac.learning_flags=1;pcm.iac.baseline_on=1;pcm.iac.baseline_off=2;
    CHECK(pcm_iac_kicker_diagnostic(&pcm)==PCM_OK && !(pcm.iac.state_flags&0x40));
    pcm.iac.learning_flags=3;CHECK(pcm_iac_kicker_diagnostic(&pcm)==PCM_OK && (pcm.iac.state_flags&0x40) && !pcm.iac.kicker_fault);
    pcm.iac.learning_flags=3;CHECK(pcm_iac_kicker_diagnostic(&pcm)==PCM_OK && pcm.iac.kicker_fault);
    pcm.iac.learning_flags=3;pcm.iac.baseline_on=3;CHECK(pcm_iac_kicker_diagnostic(&pcm)==PCM_OK && !pcm.iac.kicker_fault && !(pcm.iac.state_flags&0x40));
    INIT();cal.fault_options=8;cal.learning_count_limit=5;cal.learning_error_limit=0;
    pcm.iac.context=8;pcm.iac.rpm_error_filtered=0x100;pcm.iac.learning_count=5;
    CHECK(pcm_iac_learning_diagnostic(&pcm)==PCM_OK && pcm.iac.learning_count==6 && !pcm.iac.learning_fault);
    CHECK(pcm_iac_learning_diagnostic(&pcm)==PCM_OK && pcm.iac.learning_fault);
    cal.learning_count_limit=255;pcm.iac.learning_count=255;
    CHECK(pcm_iac_learning_diagnostic(&pcm)==PCM_OK && pcm.iac.learning_count==0 && pcm.iac.learning_fault);
    pcm.iac.bank[1].cold=1;CHECK(pcm_iac_learning_diagnostic(&pcm)==PCM_OK && !pcm.iac.learning_fault);
    INIT();pcm.runtime.spark_running=true;pcm.reference.latch_inhibited=true;pcm.scheduler.phase=0x29;
    pcm.iac.startup_rpm_adder=2;pcm.iac.startup_rpm_hold=0;pcm.iac.startup_rpm_divider=0;
    CHECK(pcm_iac_slow(&pcm)==PCM_OK && pcm.iac.startup_rpm_adder==1 && !(pcm.iac.state_flags&1));
    pcm.scheduler.phase=9;CHECK(pcm_iac_slow(&pcm)==PCM_OK && (pcm.iac.state_flags&1));
    INIT();f.platform.task[PCM_EGR_DEMAND]=NULL;pcm.iac.follower=123;
    CHECK(pcm_slot_09(&pcm)==PCM_UNIMPLEMENTED && pcm.unresolved_task==PCM_EGR_DEMAND && f.used==0 && pcm.iac.follower==123);
    INIT();f.platform.task[PCM_VSS_FILTER]=NULL;pcm.runtime.spark_running=true;
    CHECK(pcm_slot_09(&pcm)==PCM_UNIMPLEMENTED && pcm.unresolved_task==PCM_VSS_FILTER && f.used==1 && pcm.iac.follower!=0);
    INIT();pcm.runtime.spark_running=true;f.fail_at=2;
    CHECK(pcm_slot_09(&pcm)==PCM_NO_HARDWARE && f.used==1 && pcm.iac.follower!=0);
    INIT();pcm.runtime.spark_running=true;f.action=20;pcm.iac.follower=123;
    CHECK(pcm_slot_09(&pcm)==PCM_OK && pcm.iac.follower==123 && pcm.iac.target==77 && f.used==2);
    INIT();cal.follower_rpm.length=1;pcm.reference.throttle=30;pcm.iac.learning_flags=0x80;
    CHECK(pcm_iac_follower(&pcm)==PCM_BAD_CONFIGURATION && pcm.iac.follower_filtered!=0 && pcm.iac.follower==0);
    uint8_t values[]={0,255},result=77;PcmScaledCurve curve={2,0,values};
    CHECK(pcm_lookup_scaled(255,&curve,&result)==PCM_OK && result==0);
    curve.scale=255;result=77;
    CHECK(pcm_lookup_scaled(255,&curve,&result)==PCM_BAD_CONFIGURATION && result==77);
    CHECK(pcm_lookup_scaled(0,NULL,&result)==PCM_BAD_CONFIGURATION);
#undef INIT
    puts("Slow IAC stopped/phase retention, expiry calls, two-observation faults, shared reset gate and ordered slot9 dependencies pass.");
}
#ifndef IAC_SLOW_FIXTURE_ENTRY
#define IAC_SLOW_FIXTURE_ENTRY main
#endif
int IAC_SLOW_FIXTURE_ENTRY(int argc,char **argv)
{
    static Fixture f;Pcm pcm;PcmCalibration root;PcmSparkCalibration spark;
    PcmTransmissionCalibration transmission;PcmIacCalibration cal;uint8_t patterns[256],knots[256];
    if (argc==2 && strcmp(argv[1],"--contracts")==0) { slow_contracts();return 0; }
    if (argc==2 && strcmp(argv[1],"--iac-slow-defaults")==0) {
        cal=pcm_reference_iac_calibration;bool first=true;printf("[");
        for (size_t i=0;i<sizeof(slow_cal_map)/sizeof(slow_cal_map[0]);++i) {
            const Mapping *m=&slow_cal_map[i];const uint8_t *p=(const uint8_t *)&cal+m->offset;
            unsigned value=0;if (m->width==16) { uint16_t v;memcpy(&v,p,sizeof(v));value=v; }
            for (unsigned j=0;j<m->count*(m->width/8u);++j) {
                unsigned v=m->width==16?(j?value&255u:value>>8):p[j];
                printf("%s[%u,%u]",first?"":",",m->address+j,v);first=false;
            }
        }
        for (unsigned i=0;i<cal.follower_rpm.length;++i) printf(",[%u,%u]",0x5065+i,cal.follower_rpm.values[i]);
        puts("]");return 0;
    }
    if (argc==2 && strcmp(argv[1],"--follower-backing")==0) {
        printf("[");for (unsigned i=0;i<256;++i) printf("%s[%u,%u]",i?",":"",0x5065+i,slow_rpm_backing[i]);puts("]");return 0;
    }
    if (argc==2) return inherited_iac_fixture_main(argc,argv);
    unsigned mode,count;
    while (scanf("%u %u",&mode,&count)==2) {
        if (mode>12 || count>2048) return 2;
        slow_init(&f,&pcm,&root,&spark,&transmission,patterns,&cal);
        for (unsigned i=0;i<count;++i) { unsigned a,v;if (scanf("%u %u",&a,&v)!=2 || a>65535 || v>255) return 2;f.memory[a]=(uint8_t)v; }
        transfer(&pcm,f.memory,state_map,sizeof(state_map)/sizeof(state_map[0]),true);
        transfer(&pcm,f.memory,transmission_map,sizeof(transmission_map)/sizeof(transmission_map[0]),true);
        iac_state_transfer(&pcm,&f,true);transfer(&pcm,f.memory,slow_state_map,sizeof(slow_state_map)/sizeof(slow_state_map[0]),true);
        load_cal(&f,&root,&spark);memcpy(patterns,f.memory+0xb319,256);
        transfer(&cal,f.memory,iac_cal_map,sizeof(iac_cal_map)/sizeof(iac_cal_map[0]),true);
        transfer(&cal,f.memory,slow_cal_map,sizeof(slow_cal_map)/sizeof(slow_cal_map[0]),true);
        memcpy(knots,f.memory+0x5065,256);cal.follower_rpm.values=knots;cal.follower_rpm.length=256;
        f.fail_at=f.memory[0x907];f.action=f.memory[0x908];f.masked=f.memory[0x909]!=0;
        if (f.memory[0x90f]&1) f.platform.task[PCM_EGR_DEMAND]=NULL;
        if (f.memory[0x90f]&2) f.platform.task[PCM_VSS_FILTER]=NULL;
        if (f.memory[0x90a]) f.platform.task[PCM_SPARK_EXTENSION]=NULL;
        if (f.memory[0x90d]) f.platform.task[PCM_SPARK_OUTPUT_EXTENSION]=NULL;
        PcmStatus status;uint8_t value=0;
        switch (mode) {
        case 0:status=pcm_iac_follower(&pcm);break;
        case 1:status=pcm_iac_slow_decays(&pcm);break;
        case 2:status=pcm_iac_drive_limit(&pcm);break;
        case 3:status=pcm_iac_kicker_diagnostic(&pcm);break;
        case 4:status=pcm_iac_learning_diagnostic(&pcm);break;
        case 5:status=pcm_iac_reset_admit(&pcm);break;
        case 6:status=pcm_iac_reset_request(&pcm);break;
        case 7:status=pcm_iac_slow(&pcm);break;
        case 8:status=pcm_lookup_scaled(f.memory[0x900],&cal.follower_rpm,&value);break;
        case 9:case 12:status=pcm_slot_09(&pcm);break;
        case 10:status=pcm_iac_background(&pcm);if (status==PCM_OK) { pcm.scheduler.phase=9;status=pcm_iac_slow(&pcm); }break;
        default:status=pcm_iac_slow(&pcm);if (status==PCM_OK) { pcm.scheduler.phase=7;status=pcm_iac_background(&pcm); }break;
        }
        if (mode==12 && status==PCM_OK) { pcm.scheduler.phase=10;status=pcm_spark_control(&pcm); }
        transfer(&pcm,f.memory,state_map,sizeof(state_map)/sizeof(state_map[0]),false);
        transfer(&pcm,f.memory,transmission_map,sizeof(transmission_map)/sizeof(transmission_map[0]),false);
        iac_state_transfer(&pcm,&f,false);transfer(&pcm,f.memory,slow_state_map,sizeof(slow_state_map)/sizeof(slow_state_map[0]),false);
        unsigned unresolved=pcm.unresolved_task==PCM_EGR_DEMAND?7:pcm.unresolved_task==PCM_VSS_FILTER?8:
            pcm.unresolved_task==PCM_SPARK_EXTENSION?1:pcm.unresolved_task==PCM_SPARK_OUTPUT_EXTENSION?3:0;
        CHECK(pcm.unresolved_task==PCM_TASK_COUNT || unresolved!=0);
        printf("{\"status\":%u,\"value\":%u,\"state\":[",(unsigned)status,value);bool first=true;
        GROUP(command_outputs);GROUP(period_extra);GROUP(output_extra);GROUP(controller_extra);GROUP(transmission_outputs);GROUP(iac_outputs);GROUP(slow_outputs);
        printf("],\"masked\":%u,\"unresolved\":%u,\"partial\":0,\"coordinates\":[0,0],\"events\":[",(unsigned)f.masked,unresolved);
        for (unsigned i=0;i<f.used;++i) { Event *e=&f.events[i];printf("%s[\"%c\",%u,%u,%u,%u]",i?",":"",e->kind,e->width,e->address,e->value,(unsigned)e->masked); }
        puts("]}");
    }
    return 0;
}
