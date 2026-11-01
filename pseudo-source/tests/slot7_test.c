/* Reuse the existing mapped spark state/calibration and bounded I/O fixture.
 * This target links production routines; none of the resident adapters is
 * substituted. The inherited entry point keeps the older helpers referenced. */
#define main inherited_spark_fixture_main
#include "spark_test.c"
#undef main
#ifndef SLOT7_FIXTURE_ENTRY
#define SLOT7_FIXTURE_ENTRY main
#endif

#define B(a,m) {a,8,0,1,offsetof(Pcm,m)}
#define W(a,m) {a,16,0,1,offsetof(Pcm,m)}
#define F(a,b,m) {a,0,b,1,offsetof(Pcm,m)}
static const Mapping transmission_map[]={
    B(0xd9,transmission.selected_gear),B(0x4c,transmission.output_shadow),
    B(0x99,transmission.inhibit_flags),B(0x1c,transmission.fault_flags_primary),
    B(0x1d,transmission.fault_flags_secondary),F(0x86,0x01,transmission.driver_inhibit),
    B(0x8e,transmission.output_fault_flags),B(0x39a,transmission.current_service_enable),
    B(0x39b,transmission.current_service_value),B(0x8a,transmission.tcc_flags),
    B(0x8b,transmission.tcc_state),W(0x126,transmission.tcc_command),W(0x12b,transmission.tcc_lower_limit)
};
#undef B
#undef W
#undef F
static const uint16_t transmission_outputs[]={0x4c,0xd9,0x99,0x1c,0x1d,0x8e,0x8a,0x8b,
    0x126,0x127,0x12b,0x12c,0x39a,0x39b,0x306a,0x306b,0x1800,0x1801};

static PcmStatus slot_read16(void *context,uint16_t address,uint16_t *value)
{
    if (address!=PCM_EXTENSION_SIGNATURE) return read16(context,address,value);
    Fixture *f=context;uint16_t sample=word(f->memory,address);
    PcmStatus result=record(f,'R',16,address,sample);
    if (result==PCM_OK) {
        *value=sample;
        if (f->action==17) {
            f->pcm->scheduler.profiling_enabled=true;
            f->pcm->transmission.output_shadow^=0x55;
        }
    }
    return result;
}
static PcmStatus slot_write16(void *context,uint16_t address,uint16_t value)
{
    if (address!=PCM_TCC_COMMAND) return write16(context,address,value);
    Fixture *f=context;PcmStatus result=record(f,'W',16,address,value);
    if (result==PCM_OK) {
        f->memory[address]=(uint8_t)(value>>8);f->memory[address+1]=(uint8_t)value;
        if (f->action==18) { f->pcm->transmission.tcc_command=0x9abc;f->pcm->transmission.tcc_flags=0; }
    }
    return result;
}
static PcmStatus slot_dependency(Pcm *pcm,PcmTask task)
{
    Fixture *f=pcm->platform->context;
    CHECK(task==PCM_CONNECTION_EXTENSION || task==PCM_IAC_BACKGROUND || task==PCM_SHIFT_LAMP);
    uint16_t address=task==PCM_CONNECTION_EXTENSION?0x180c:task==PCM_IAC_BACKGROUND?0x9e99:0xaca7;
    PcmStatus result=record(f,'T',0,address,(uint16_t)f->action);
    if (result!=PCM_OK) return result;
    if (task==PCM_CONNECTION_EXTENSION) {
        if (f->action==13) { pcm->scheduler.profiling_enabled=true;pcm->transmission.output_shadow^=0x55; }
        if (f->action==14) { pcm->scheduler.profiling_enabled=false;pcm->reference.coolant=32; }
    } else if (task==PCM_IAC_BACKGROUND && f->action==15) {
        pcm->reference.coolant=200;pcm->runtime.power_enrichment=true;pcm->spark.pe_fraction=123;
        pcm->spark.mat_sample=140;pcm->spark.load_coordinate=128;pcm->reference.rpm_coordinate=180;
        pcm->knock.sensor_fault=true;
    } else if (task==PCM_SHIFT_LAMP && f->action==16) {
        pcm->spark.command=0xbeef;pcm->transmission.output_shadow^=0xa0;
    }
    return PCM_OK;
}
static void slot_init(Fixture *f,Pcm *pcm,PcmCalibration *root,PcmSparkCalibration *spark,
                      PcmTransmissionCalibration *transmission,uint8_t *patterns)
{
    init(f,pcm,root,spark);bind(f,pcm);
    *transmission=pcm_reference_transmission_calibration;
    CHECK(transmission->gear_pattern_length==256);
    memcpy(patterns,transmission->gear_patterns,256);memcpy(f->memory+0xb319,patterns,256);
    transmission->gear_patterns=patterns;root->transmission=transmission;
    f->platform.read16=slot_read16;f->platform.write16=slot_write16;
    f->platform.task[PCM_CONNECTION_EXTENSION]=slot_dependency;
    f->platform.task[PCM_IAC_BACKGROUND]=slot_dependency;
    f->platform.task[PCM_SHIFT_LAMP]=slot_dependency;
    f->platform.task[PCM_SLOT_07]=NULL;
}
static void slot_contracts(void)
{
    static Fixture f;Pcm pcm;PcmCalibration root;PcmSparkCalibration spark;
    PcmTransmissionCalibration transmission;uint8_t patterns[256];
    slot_init(&f,&pcm,&root,&spark,&transmission,patterns);
    pcm.transmission.output_shadow=0xab;pcm.transmission.tcc_state=0xff;root.transmission=NULL;
    CHECK(pcm_transmission_outputs(&pcm)==PCM_BAD_CONFIGURATION && pcm.transmission.output_shadow==0xab && f.used==0);
    root.transmission=&transmission;transmission.gear_patterns=NULL;
    CHECK(pcm_transmission_outputs(&pcm)==PCM_BAD_CONFIGURATION && pcm.transmission.tcc_state==0xff);
    transmission.gear_patterns=patterns;transmission.gear_pattern_length=3;pcm.transmission.selected_gear=3;
    CHECK(pcm_transmission_outputs(&pcm)==PCM_BAD_CONFIGURATION && pcm.transmission.output_shadow==0xab);
    slot_init(&f,&pcm,&root,&spark,&transmission,patterns);pcm.platform=NULL;root.mode_f=0x40;
    pcm.transmission.tcc_state=0xff;pcm.transmission.output_shadow=0xcc;
    CHECK(pcm_transmission_outputs(&pcm)==PCM_OK && pcm.transmission.output_shadow==0xed && pcm.transmission.tcc_state==0xff);
    slot_init(&f,&pcm,&root,&spark,&transmission,patterns);f.fail_at=1;
    pcm.transmission.tcc_command=0x8123;pcm.transmission.tcc_flags=4;pcm.transmission.tcc_state=0xa4;
    CHECK(pcm_transmission_outputs(&pcm)==PCM_NO_HARDWARE && pcm.transmission.output_shadow==0x21);
    CHECK(pcm.transmission.tcc_state==0xa5 && f.used==0);
    slot_init(&f,&pcm,&root,&spark,&transmission,patterns);pcm.calibration=NULL;
    CHECK(pcm_connection_probe(&pcm)==PCM_OK && f.used==1); /* No profile or0086.6 gate. */
    f.memory[0x1800]=0x7e;f.memory[0x1801]=0x18;f.platform.task[PCM_CONNECTION_EXTENSION]=NULL;
    CHECK(pcm_connection_probe(&pcm)==PCM_UNIMPLEMENTED && pcm.unresolved_task==PCM_CONNECTION_EXTENSION && f.used==2);
    for (unsigned fail=1;fail<=5;++fail) {
        slot_init(&f,&pcm,&root,&spark,&transmission,patterns);f.fail_at=fail;
        f.memory[0x1800]=0x7e;f.memory[0x1801]=0x18;
        CHECK(pcm_slot_07(&pcm)==PCM_NO_HARDWARE && f.used==fail-1u);
    }
    slot_init(&f,&pcm,&root,&spark,&transmission,patterns);
    f.memory[0x1800]=0x7e;f.memory[0x1801]=0x18;f.action=13;
    CHECK(pcm_slot_07(&pcm)==PCM_OK && pcm.scheduler.profiling_enabled && f.used==5);
    CHECK(f.events[0].address==PCM_TCC_COMMAND && f.events[1].address==PCM_EXTENSION_SIGNATURE &&
          f.events[2].address==0x180c && f.events[3].address==0x9e99 && f.events[4].address==0xaca7);
    slot_init(&f,&pcm,&root,&spark,&transmission,patterns);f.platform.task[PCM_IAC_BACKGROUND]=NULL;
    pcm.spark.pe_advance=77;CHECK(pcm_slot_07(&pcm)==PCM_UNIMPLEMENTED && f.used==2 && pcm.spark.pe_advance==77);
    CHECK(pcm.unresolved_task==PCM_IAC_BACKGROUND);
    slot_init(&f,&pcm,&root,&spark,&transmission,patterns);f.platform.task[PCM_SHIFT_LAMP]=NULL;
    pcm.spark.pe_advance=77;CHECK(pcm_slot_07(&pcm)==PCM_UNIMPLEMENTED && f.used==3 && pcm.spark.pe_advance==0);
    CHECK(pcm.unresolved_task==PCM_SHIFT_LAMP);
    puts("Slot7 profile bounds, retained mode route, failed output prefixes, signature gate and ordered dependencies pass.");
}
static void print_group(const Fixture *f,const uint16_t *addresses,size_t count,bool *first)
{
    for (size_t i=0;i<count;++i) { printf("%s%u",*first?"":",",f->memory[addresses[i]]);*first=false; }
}
#define GROUP(a) print_group(&f,a,sizeof(a)/sizeof(a[0]),&first)
int SLOT7_FIXTURE_ENTRY(int argc,char **argv)
{
    static Fixture f;Pcm pcm;PcmCalibration root;PcmSparkCalibration spark;
    PcmTransmissionCalibration transmission;uint8_t patterns[256];
    if (argc==2 && strcmp(argv[1],"--contracts")==0) { slot_contracts();return 0; }
    if (argc==2 && strcmp(argv[1],"--defaults")==0) return inherited_spark_fixture_main(argc,argv);
    if (argc==2 && strcmp(argv[1],"--slot7-defaults")==0) {
        printf("[[16399,%u]",pcm_reference_scheduler_calibration.mode_f);
        for (unsigned i=0;i<256;++i) printf(",[%u,%u]",0xb319+i,pcm_reference_transmission_calibration.gear_patterns[i]);
        puts("]");return 0;
    }
    unsigned mode,count;
    while (scanf("%u %u",&mode,&count)==2) {
        if (mode>3 || count>2048) return 2;
        slot_init(&f,&pcm,&root,&spark,&transmission,patterns);
        for (unsigned i=0;i<count;++i) {
            unsigned a,v;if (scanf("%u %u",&a,&v)!=2 || a>65535 || v>255) return 2;f.memory[a]=(uint8_t)v;
        }
        transfer(&pcm,f.memory,state_map,sizeof(state_map)/sizeof(state_map[0]),true);
        transfer(&pcm,f.memory,transmission_map,sizeof(transmission_map)/sizeof(transmission_map[0]),true);
        load_cal(&f,&root,&spark);memcpy(patterns,f.memory+0xb319,256);
        f.fail_at=f.memory[0x907];f.action=f.memory[0x908];f.masked=f.memory[0x909]!=0;
        if (f.memory[0x90a]) f.platform.task[PCM_SPARK_EXTENSION]=NULL;
        if (f.memory[0x90d]) f.platform.task[PCM_SPARK_OUTPUT_EXTENSION]=NULL;
        if (f.memory[0x90e]&1) f.platform.task[PCM_CONNECTION_EXTENSION]=NULL;
        if (f.memory[0x90e]&2) f.platform.task[PCM_IAC_BACKGROUND]=NULL;
        if (f.memory[0x90e]&4) f.platform.task[PCM_SHIFT_LAMP]=NULL;
        PcmStatus status=mode==0?pcm_transmission_outputs(&pcm):mode==1?pcm_connection_probe(&pcm):pcm_slot_07(&pcm);
        if (mode==3 && status==PCM_OK) { pcm.scheduler.phase=8;status=pcm_spark_control(&pcm); }
        transfer(&pcm,f.memory,state_map,sizeof(state_map)/sizeof(state_map[0]),false);
        transfer(&pcm,f.memory,transmission_map,sizeof(transmission_map)/sizeof(transmission_map[0]),false);
        unsigned unresolved=pcm.unresolved_task==PCM_SPARK_EXTENSION?1:pcm.unresolved_task==PCM_SPARK_OUTPUT_EXTENSION?3:
            pcm.unresolved_task==PCM_CONNECTION_EXTENSION?4:pcm.unresolved_task==PCM_IAC_BACKGROUND?5:
            pcm.unresolved_task==PCM_SHIFT_LAMP?6:0;
        CHECK(pcm.unresolved_task==PCM_TASK_COUNT || unresolved!=0);
        printf("{\"status\":%u,\"value\":0,\"state\":[",(unsigned)status);bool first=true;
        GROUP(command_outputs);GROUP(period_extra);GROUP(output_extra);GROUP(controller_extra);GROUP(transmission_outputs);
        printf("],\"masked\":%u,\"unresolved\":%u,\"partial\":0,\"coordinates\":[0,0],\"events\":[",(unsigned)f.masked,unresolved);
        for (unsigned i=0;i<f.used;++i) { Event *e=&f.events[i];printf("%s[\"%c\",%u,%u,%u,%u]",i?",":"",e->kind,e->width,e->address,e->value,(unsigned)e->masked); }
        puts("]}");
    }
    return 0;
}
