#define SLOT7_FIXTURE_ENTRY inherited_slot7_fixture_main
#include "slot7_test.c"
#include "iac.h"
#include "iac_fixture_map.h"

static void iac_state_transfer(Pcm *pcm,Fixture *f,bool load)
{
    for (size_t i=0;i<sizeof(iac_state_map)/sizeof(iac_state_map[0]);++i) {
        const Mapping *m=&iac_state_map[i];
        if (m->width==7) {
            volatile uint8_t *field=(volatile uint8_t *)(void *)((uint8_t *)pcm+m->offset);
            if (load) *field=f->memory[m->address]&m->mask;
            else f->memory[m->address]=(uint8_t)((f->memory[m->address]&(uint8_t)~m->mask)|(*field&m->mask));
        } else transfer(pcm,f->memory,m,1,load);
    }
}
static PcmStatus iac_read8(void *context,uint16_t address,uint8_t *value)
{
    if (address!=PCM_PORTD) return read8(context,address,value);
    Fixture *f=context;uint8_t sample=f->memory[address];
    PcmStatus result=record(f,'R',8,address,sample);
    if (result==PCM_OK) {
        *value=sample;
        if (f->action==19) {
            f->pcm->iac.context=3;f->pcm->spark.iac_desired_speed=250;
            f->pcm->iac.slewed_base=0x55;f->pcm->iac.switch_offset=7;f->pcm->iac.switch_delay=2;
        }
    }
    return result;
}
static void iac_init(Fixture *f,Pcm *pcm,PcmCalibration *root,PcmSparkCalibration *spark,
                     PcmTransmissionCalibration *transmission,uint8_t *patterns,PcmIacCalibration *cal)
{
    slot_init(f,pcm,root,spark,transmission,patterns);
    *cal=pcm_reference_iac_calibration;root->iac=cal;f->platform.read8=iac_read8;
    f->platform.task[PCM_IAC_BACKGROUND]=NULL;
    for (size_t i=0;i<sizeof(iac_cal_map)/sizeof(iac_cal_map[0]);++i) {
        const Mapping *m=&iac_cal_map[i];const uint8_t *value=(const uint8_t *)cal+m->offset;
        for (unsigned j=0;j<m->count;++j) put(f,m->address+j,value[j]);
    }
}
static void iac_contracts(void)
{
    static Fixture f;Pcm pcm;PcmCalibration root;PcmSparkCalibration spark;
    PcmTransmissionCalibration transmission;PcmIacCalibration cal;uint8_t patterns[256];
#define INIT() iac_init(&f,&pcm,&root,&spark,&transmission,patterns,&cal)
    INIT();pcm.calibration=NULL;pcm.iac.context=3;pcm.iac.bank[1].ac_snapshot=99;
    pcm.iac.hold[0]=7;pcm.iac.hold[1]=9;pcm.spark.iac_desired_speed=17;
    CHECK(pcm_iac_background(&pcm)==PCM_OK && pcm.iac.selected_snapshot==99 && pcm.iac.hold[0]==7);
    CHECK(pcm.spark.iac_desired_speed==17 && f.used==0 && pcm.unresolved_task==PCM_TASK_COUNT);
    pcm.runtime.spark_running=true;CHECK(pcm_iac_background(&pcm)==PCM_BAD_CONFIGURATION && pcm.iac.selected_snapshot==99);
    INIT();pcm.iac.transfer_flags=0x40;pcm.calibration=NULL;pcm.iac.stall_threshold=33;
    CHECK(pcm_iac_desired(&pcm)==PCM_OK && pcm.iac.stall_threshold==33);
    INIT();pcm.iac.kicker_flags=4;pcm.calibration=NULL;pcm.iac.kicker_request=true;
    CHECK(pcm_iac_kicker_enable(&pcm)==PCM_OK && !pcm.iac.kicker_request);
    pcm.iac.kicker_flags=0;CHECK(pcm_iac_kicker_enable(&pcm)==PCM_BAD_CONFIGURATION);
    INIT();pcm.iac.tps_zero_low=123;pcm.iac.baseline_on=250;cal.kicker_tps_adder=20;
    CHECK(pcm_iac_kicker_enable(&pcm)==PCM_OK && pcm.iac.tps_zero_high==14 && pcm.iac.tps_zero_low==123);
    pcm.iac.kicker_timer=77;CHECK(pcm_iac_kicker_disable(&pcm)==PCM_OK && pcm.iac.kicker_timer==0 && pcm.iac.kicker_request);
    pcm.iac.kicker_timer=88;CHECK(pcm_iac_kicker_disable(&pcm)==PCM_OK && pcm.iac.kicker_timer==88);
    INIT();pcm.spark.vehicle_speed_high=255;pcm.iac.bank[0].cold=12345;
    CHECK(pcm_iac_movement(&pcm)==PCM_OK && pcm.iac.bank[0].cold==12345 && !(pcm.iac.state_flags&2));
    cal.movement_speed_limit=0;pcm.spark.vehicle_speed_high=1;cal.movement_gain=128;
    CHECK(pcm_iac_movement(&pcm)==PCM_OK && pcm.iac.bank[0].cold==6173 && (pcm.iac.state_flags&2));
    pcm.iac.dfco_adder=3;pcm.iac.dfco_divider=1;pcm.iac.transfer_flags=0x20;
    CHECK(pcm_iac_movement(&pcm)==PCM_OK && pcm.iac.dfco_adder==0 && (pcm.iac.transfer_flags&0x20));
    pcm.iac.dfco_adder=2;pcm.iac.dfco_divider=1;
    CHECK(pcm_iac_movement(&pcm)==PCM_OK && !(pcm.iac.transfer_flags&0x20));
    INIT();pcm.runtime.spark_running=true;pcm.iac.context=0x0c;
    CHECK(pcm_iac_background(&pcm)==PCM_OK && pcm.unresolved_task==PCM_TASK_COUNT);
    INIT();cal.options|=0x10;cal.switch_threshold[0]=255;f.fail_at=1;
    pcm.spark.iac_desired_speed=7;pcm.iac.stall_threshold=9;pcm.iac.switch_offset=3;pcm.iac.slewed_base=0;
    CHECK(pcm_iac_desired(&pcm)==PCM_NO_HARDWARE && pcm.spark.iac_desired_speed==7 && pcm.iac.stall_threshold==9);
    CHECK(pcm.iac.slewed_base!=0 && pcm.iac.switch_offset==3 && f.used==0);
    INIT();pcm.iac.context=8;pcm.iac.bank[0].no_ac=0xff00;pcm.iac.bank[0].ac=0;
    CHECK(pcm_iac_transfer(&pcm)==PCM_OK && pcm.iac.proposed[0][1]==65535);
    CHECK(pcm.iac.bank[0].no_ac==0xff00 && pcm.iac.bank[0].ac==0);
    INIT();
    for (unsigned i=0;i<4;++i) for (unsigned j=0;j<17;++j) cal.rpm_curve[i][j]=20;
    cal.battery_threshold=0;cal.rough_gain=255;pcm.iac.rpm_error_filtered=0x0100;
    pcm.iac.blm_cell_index=16;pcm.iac.blm_value=0;pcm.reference.coolant=255;
    cal.blm_limit=1;cal.blm_coolant_minimum=0;cal.blm_count_limit=5;cal.blm_adder[0]=4;
    pcm.iac.blm_count=4;pcm.scheduler.phase=7;
    CHECK(pcm_iac_desired(&pcm)==PCM_OK && pcm.iac.blm_count==5 && pcm.spark.iac_desired_speed==20);
    CHECK(pcm_iac_desired(&pcm)==PCM_OK && pcm.spark.iac_desired_speed==24);
    for (unsigned sample=0;sample<=4;sample+=4) {
        INIT();for (unsigned i=0;i<4;++i) for (unsigned j=0;j<17;++j) cal.rpm_curve[i][j]=20;
        cal.options=0x10;cal.battery_threshold=0;cal.rough_gain=0;
        cal.switch_threshold[0]=100;cal.switch_threshold[1]=200;cal.stall_factor[3]=128;
        f.action=19;f.memory[PCM_PORTD]=(uint8_t)sample;pcm.spark.iac_desired_speed=77;
        CHECK(pcm_iac_desired(&pcm)==PCM_OK && f.used==1 && pcm.iac.slewed_base==0x55);
        CHECK(pcm.spark.iac_desired_speed==(sample?100:92) && pcm.iac.stall_threshold==(sample?50:46));
        CHECK(pcm.iac.switch_offset==7 && pcm.iac.switch_delay==(sample?2:1));
    }
#undef INIT
    puts("Background IAC stopped/override retention, shared-byte fields, high-byte TPS update, stock closed gate and prefix contracts pass.");
}
int main(int argc,char **argv)
{
    static Fixture f;Pcm pcm;PcmCalibration root;PcmSparkCalibration spark;
    PcmTransmissionCalibration transmission;PcmIacCalibration cal;uint8_t patterns[256];
    if (argc==2 && strcmp(argv[1],"--contracts")==0) { iac_contracts();return 0; }
    if (argc==2 && (strcmp(argv[1],"--defaults")==0 || strcmp(argv[1],"--slot7-defaults")==0))
        return inherited_slot7_fixture_main(argc,argv);
    if (argc==2 && strcmp(argv[1],"--iac-defaults")==0) {
        iac_init(&f,&pcm,&root,&spark,&transmission,patterns,&cal);
        bool seen[65536]={0},first=true;printf("[");
        for (size_t i=0;i<sizeof(iac_cal_map)/sizeof(iac_cal_map[0]);++i)
            for (unsigned j=0;j<iac_cal_map[i].count;++j) {
                unsigned a=iac_cal_map[i].address+j;if (seen[a]) continue;seen[a]=true;
                printf("%s[%u,%u]",first?"":",",a,f.memory[a]);first=false;
            }
        puts("]");return 0;
    }
    unsigned mode,count;
    while (scanf("%u %u",&mode,&count)==2) {
        if (mode>12 || count>2048) return 2;
        iac_init(&f,&pcm,&root,&spark,&transmission,patterns,&cal);
        for (unsigned i=0;i<count;++i) {
            unsigned a,v;if (scanf("%u %u",&a,&v)!=2 || a>65535 || v>255) return 2;f.memory[a]=(uint8_t)v;
        }
        transfer(&pcm,f.memory,state_map,sizeof(state_map)/sizeof(state_map[0]),true);
        transfer(&pcm,f.memory,transmission_map,sizeof(transmission_map)/sizeof(transmission_map[0]),true);
        iac_state_transfer(&pcm,&f,true);load_cal(&f,&root,&spark);memcpy(patterns,f.memory+0xb319,256);
        transfer(&cal,f.memory,iac_cal_map,sizeof(iac_cal_map)/sizeof(iac_cal_map[0]),true);
        f.fail_at=f.memory[0x907];f.action=f.memory[0x908];f.masked=f.memory[0x909]!=0;
        if (f.memory[0x90a]) f.platform.task[PCM_SPARK_EXTENSION]=NULL;
        if (f.memory[0x90d]) f.platform.task[PCM_SPARK_OUTPUT_EXTENSION]=NULL;
        if (f.memory[0x90e]&1) f.platform.task[PCM_CONNECTION_EXTENSION]=NULL;
        if (f.memory[0x90e]&4) f.platform.task[PCM_SHIFT_LAMP]=NULL;
        PcmStatus status;
        switch (mode) {
        case 0:status=pcm_iac_desired(&pcm);break;
        case 1:status=pcm_iac_kicker_disable(&pcm);break;
        case 2:status=pcm_iac_kicker_enable(&pcm);break;
        case 3:status=pcm_iac_movement(&pcm);break;
        case 4:status=pcm_iac_kicker(&pcm);break;
        case 5:status=pcm_iac_cold(&pcm);break;
        case 6:status=pcm_iac_transition_decay(&pcm);break;
        case 7:status=pcm_iac_transfer(&pcm);break;
        case 8:case 9:status=pcm_iac_publish(&pcm,mode==8);break;
        case 10:status=pcm_iac_background(&pcm);break;
        default:status=pcm_slot_07(&pcm);break;
        }
        if (mode==12 && status==PCM_OK) { pcm.scheduler.phase=8;status=pcm_spark_control(&pcm); }
        transfer(&pcm,f.memory,state_map,sizeof(state_map)/sizeof(state_map[0]),false);
        transfer(&pcm,f.memory,transmission_map,sizeof(transmission_map)/sizeof(transmission_map[0]),false);
        iac_state_transfer(&pcm,&f,false);
        unsigned unresolved=pcm.unresolved_task==PCM_SPARK_EXTENSION?1:pcm.unresolved_task==PCM_SPARK_OUTPUT_EXTENSION?3:
            pcm.unresolved_task==PCM_CONNECTION_EXTENSION?4:pcm.unresolved_task==PCM_SHIFT_LAMP?6:0;
        CHECK(pcm.unresolved_task==PCM_TASK_COUNT || unresolved!=0);
        printf("{\"status\":%u,\"value\":0,\"state\":[",(unsigned)status);bool first=true;
        GROUP(command_outputs);GROUP(period_extra);GROUP(output_extra);GROUP(controller_extra);GROUP(transmission_outputs);GROUP(iac_outputs);
        printf("],\"masked\":%u,\"unresolved\":%u,\"partial\":0,\"coordinates\":[0,0],\"events\":[",(unsigned)f.masked,unresolved);
        for (unsigned i=0;i<f.used;++i) { Event *e=&f.events[i];printf("%s[\"%c\",%u,%u,%u,%u]",i?",":"",e->kind,e->width,e->address,e->value,(unsigned)e->masked); }
        puts("]}");
    }
    return 0;
}
