#define IAC_MAIN_FIXTURE_ENTRY inherited_main_fixture_main
#include "iac_main_test.c"

static PcmStatus step_mask(void *context,bool masked)
{
    Fixture *f=context;PcmStatus result=mask(context,masked);
    if (result!=PCM_OK) return result;
    if (masked && f->action==25) { f->pcm->iac.step_control=0xe7;f->pcm->transmission.output_shadow=0xa3; }
    if (!masked && f->action==26) { f->pcm->iac.step_control=0xb8;f->pcm->transmission.output_shadow=0x5a; }
    if (masked && f->action==27) {
        f->pcm->iac.step_control=0xfe;f->pcm->transmission.output_shadow=0x63;
        f->pcm->iac.position=77;f->pcm->iac.target=99;f->pcm->scheduler.phase=3;
    }
    return PCM_OK;
}
static void step_init(Fixture *f,Pcm *pcm,PcmCalibration *root,PcmSparkCalibration *spark,
                      PcmTransmissionCalibration *transmission,uint8_t *patterns,PcmIacCalibration *cal)
{
    main_init(f,pcm,root,spark,transmission,patterns,cal);
    f->memory[0x4eb6]=cal->step_battery_minimum;
    f->platform.mask_irq=step_mask;f->platform.task[PCM_IAC_STEP]=NULL;
}
static void step_contracts(void)
{
    static Fixture f;Pcm pcm;PcmCalibration root;PcmSparkCalibration spark;
    PcmTransmissionCalibration transmission;PcmIacCalibration cal;uint8_t patterns[256];
#define INIT() step_init(&f,&pcm,&root,&spark,&transmission,patterns,&cal)
    INIT();pcm.iac.position=20;pcm.iac.target=30;pcm.iac.step_control=0x10;pcm.spark.battery_sample=105;
    CHECK(pcm_iac_step(&pcm)==PCM_OK && pcm.iac.low_battery && pcm.iac.position==20 && pcm.iac.step_control==0x10);
    CHECK((pcm.transmission.output_shadow&0x1c)==0x10 && !f.masked && f.used==2);
    pcm.spark.battery_sample=170;pcm.calibration=NULL;
    CHECK(pcm_iac_step(&pcm)==PCM_OK && pcm.iac.low_battery && pcm.iac.step_control==0 && pcm.iac.position==20);
    pcm.reference.latch_inhibited=true;pcm.spark.battery_sample=0;
    CHECK(pcm_iac_step(&pcm)==PCM_OK && !pcm.iac.low_battery && pcm.iac.position==21);
    INIT();pcm.calibration=NULL;pcm.iac.step_control=0xff;pcm.iac.position=20;pcm.spark.battery_sample=169;
    CHECK(pcm_iac_step(&pcm)==PCM_BAD_CONFIGURATION && pcm.iac.step_control==0xff && pcm.iac.position==20 && f.used==0);
    INIT();pcm.spark.battery_sample=130;pcm.iac.position=20;pcm.iac.target=30;pcm.iac.step_control=1;
    CHECK(pcm_iac_step(&pcm)==PCM_OK && pcm.iac.position==20 && pcm.iac.step_control==0x10);
    CHECK(pcm_iac_step(&pcm)==PCM_OK && pcm.iac.position==21 && (pcm.iac.step_control&0xc)==4);
    pcm.iac.target=21;pcm.iac.step_control|=1;
    CHECK(pcm_iac_step(&pcm)==PCM_OK && pcm.iac.position==21 && !(pcm.iac.step_control&1) && (pcm.iac.step_control&0xc)==4);
    INIT();pcm.spark.battery_sample=130;pcm.iac.position=100;pcm.iac.target=200;
    static const unsigned ring[]={4,12,8,0};
    for (unsigned i=0;i<8;++i) { CHECK(pcm_iac_step(&pcm)==PCM_OK);CHECK((pcm.iac.step_control&12)==ring[i%4] && pcm.iac.position==101+i); }
    pcm.iac.target=0;CHECK(pcm_iac_step(&pcm)==PCM_OK && pcm.iac.position==108 && (pcm.iac.step_control&12)==0);
    for (unsigned i=0;i<4;++i) { CHECK(pcm_iac_step(&pcm)==PCM_OK);CHECK((pcm.iac.step_control&12)==ring[(2-i)&3] && pcm.iac.position==107-i); }
    for (unsigned phase=0;phase<4;++phase) {
        INIT();pcm.spark.battery_sample=130;pcm.iac.position=20;pcm.iac.target=30;pcm.iac.state_flags=1;pcm.scheduler.phase=(uint8_t)phase;
        CHECK(pcm_iac_step(&pcm)==PCM_OK && pcm.iac.position==(phase==3?20:21));
    }
    for (unsigned fail=1;fail<=2;++fail) {
        INIT();pcm.spark.battery_sample=130;pcm.iac.position=20;pcm.iac.target=30;pcm.transmission.output_shadow=0xe3;f.fail_at=fail;
        CHECK(pcm_iac_step(&pcm)==PCM_NO_HARDWARE && pcm.iac.position==21 && pcm.iac.step_control==0x14);
        CHECK(pcm.transmission.output_shadow==(fail==1?0xe3:0xf7) && f.masked==(fail==2));
    }
    INIT();pcm.spark.battery_sample=130;pcm.iac.position=20;pcm.iac.target=30;f.platform.mask_irq=NULL;
    CHECK(pcm_iac_step(&pcm)==PCM_NO_HARDWARE && pcm.iac.position==21 && pcm.iac.step_control==0x14);
    INIT();pcm.spark.battery_sample=130;pcm.iac.position=20;pcm.iac.target=30;f.action=25;f.masked=true;
    CHECK(pcm_iac_step(&pcm)==PCM_OK && pcm.iac.step_control==0xe7 && pcm.transmission.output_shadow==0xb7 && !f.masked);
    CHECK(f.events[0].masked && f.events[0].value==1 && f.events[1].masked && f.events[1].value==0);
    INIT();pcm.spark.battery_sample=130;pcm.iac.position=20;pcm.iac.target=30;f.action=27;
    CHECK(pcm_iac_step(&pcm)==PCM_OK && pcm.iac.position==77 && pcm.iac.target==99 && pcm.iac.step_control==0xfe);
    CHECK(pcm.transmission.output_shadow==0x77 && pcm.scheduler.phase==3);
    INIT();pcm.spark.battery_sample=130;f.action=26;
    CHECK(pcm_iac_step(&pcm)==PCM_OK && pcm.transmission.output_shadow==0x5a && pcm.iac.step_control==0xb8);
#undef INIT
    puts("IAC step voltage gates, reversal pause, four-state ring, reset admission and literal-mask failure prefixes pass.");
}
int main(int argc,char **argv)
{
    static Fixture f;Pcm pcm;PcmCalibration root;PcmSparkCalibration spark;
    PcmTransmissionCalibration transmission;PcmIacCalibration cal;uint8_t patterns[256],baro[256],mat[256],ae[256],rpm[256];
    if (argc==2 && strcmp(argv[1],"--contracts")==0) { step_contracts();return 0; }
    if (argc==2 && strcmp(argv[1],"--step-defaults")==0) { printf("[[%u,%u]]\n",0x4eb6,pcm_reference_iac_calibration.step_battery_minimum);return 0; }
    if (argc==2) return inherited_main_fixture_main(argc,argv);
    unsigned mode,count;
    while (scanf("%u %u",&mode,&count)==2) {
        if (mode>9 || count>2048) return 2;
        step_init(&f,&pcm,&root,&spark,&transmission,patterns,&cal);
        for (unsigned i=0;i<count;++i) { unsigned a,v;if (scanf("%u %u",&a,&v)!=2 || a>65535 || v>255) return 2;f.memory[a]=(uint8_t)v; }
        transfer(&pcm,f.memory,state_map,sizeof(state_map)/sizeof(state_map[0]),true);
        transfer(&pcm,f.memory,transmission_map,sizeof(transmission_map)/sizeof(transmission_map[0]),true);
        iac_state_transfer(&pcm,&f,true);transfer(&pcm,f.memory,slow_state_map,sizeof(slow_state_map)/sizeof(slow_state_map[0]),true);
        transfer(&pcm,f.memory,main_state_map,sizeof(main_state_map)/sizeof(main_state_map[0]),true);
        pcm.iac.step_control=f.memory[10];
        load_cal(&f,&root,&spark);memcpy(patterns,f.memory+0xb319,256);
        transfer(&cal,f.memory,iac_cal_map,sizeof(iac_cal_map)/sizeof(iac_cal_map[0]),true);
        transfer(&cal,f.memory,slow_cal_map,sizeof(slow_cal_map)/sizeof(slow_cal_map[0]),true);
        transfer(&cal,f.memory,main_cal_map,sizeof(main_cal_map)/sizeof(main_cal_map[0]),true);
        cal.step_battery_minimum=f.memory[0x4eb6];
#define LOAD_BACKING(a,c,v) memcpy(v,f.memory+(a),256);(c).values=(v);(c).length=256
        LOAD_BACKING(0x4ea6,cal.baro.curve,baro);LOAD_BACKING(0x4f17,cal.ac_temperature.curve,mat);
        LOAD_BACKING(0x50a3,cal.enrichment_curve,ae);LOAD_BACKING(0x5065,cal.follower_rpm,rpm);
#undef LOAD_BACKING
        f.fail_at=f.memory[0x907];f.action=f.memory[0x908];f.masked=f.memory[0x909]!=0;
        PcmStatus status=PCM_OK;
#define RUN(call) do { status=(call);if (status!=PCM_OK) goto finished; } while (0)
        switch (mode) {
        case 0:RUN(pcm_iac_step(&pcm));break;
        case 1:RUN(pcm_iac_step(&pcm));RUN(pcm_iac_control(&pcm));break;
        case 2:RUN(pcm_iac_control(&pcm));RUN(pcm_iac_step(&pcm));break;
        case 3:RUN(pcm_iac_step(&pcm));RUN(pcm_iac_background(&pcm));break;
        case 4:RUN(pcm_iac_background(&pcm));RUN(pcm_iac_step(&pcm));break;
        case 5:RUN(pcm_iac_step(&pcm));RUN(pcm_transmission_outputs(&pcm));break;
        case 6:RUN(pcm_transmission_outputs(&pcm));RUN(pcm_iac_step(&pcm));break;
        case 7:for (unsigned i=0;i<16;++i) { RUN(pcm_iac_step(&pcm));if (i<15) pcm.scheduler.phase=(uint8_t)((pcm.scheduler.phase+1u)%160u); }break;
        case 8:RUN(pcm_iac_step(&pcm));RUN(pcm_iac_slow(&pcm));break;
        default:RUN(pcm_iac_slow(&pcm));RUN(pcm_iac_step(&pcm));break;
        }
finished:
#undef RUN
        transfer(&pcm,f.memory,state_map,sizeof(state_map)/sizeof(state_map[0]),false);
        transfer(&pcm,f.memory,transmission_map,sizeof(transmission_map)/sizeof(transmission_map[0]),false);
        iac_state_transfer(&pcm,&f,false);transfer(&pcm,f.memory,slow_state_map,sizeof(slow_state_map)/sizeof(slow_state_map[0]),false);
        transfer(&pcm,f.memory,main_state_map,sizeof(main_state_map)/sizeof(main_state_map[0]),false);
        f.memory[10]=pcm.iac.step_control;
        CHECK(pcm.unresolved_task==PCM_TASK_COUNT);
        printf("{\"status\":%u,\"value\":0,\"state\":[",(unsigned)status);bool first=true;
        GROUP(command_outputs);GROUP(period_extra);GROUP(output_extra);GROUP(controller_extra);GROUP(transmission_outputs);GROUP(iac_outputs);GROUP(slow_outputs);GROUP(main_outputs);
        printf(",%u],\"masked\":%u,\"unresolved\":0,\"partial\":0,\"coordinates\":[0,0],\"events\":[",f.memory[10],(unsigned)f.masked);
        for (unsigned i=0;i<f.used;++i) { Event *e=&f.events[i];printf("%s[\"%c\",%u,%u,%u,%u]",i?",":"",e->kind,e->width,e->address,e->value,(unsigned)e->masked); }
        puts("]}");
    }
    return 0;
}
