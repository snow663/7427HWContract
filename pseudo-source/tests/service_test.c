#define PCM_SERIAL_TEST_MAIN inherited_serial_main
#include "serial_test.c"
#undef PCM_SERIAL_TEST_MAIN
#include "service.h"
#include "spark.h"
#include "service_fixture_map.h"

static void service_transfer(Pcm *pcm,Fixture *f,bool load)
{
    serial_transfer(pcm,f,load);transfer(pcm,f->memory,service_state_map,SIZE(service_state_map),load);
}
/* C calls here are logical data accesses, not native field loads or fetches. */
static PcmStatus service_read8(void *v,uint16_t a,uint8_t *out)
{
    Fixture *f=v;service_transfer(f->pcm,f,false);uint8_t value=f->memory[a];
    PcmStatus r=record(f,'R',8,a,value);if (r!=PCM_OK) return r;*out=value;
    if (f->action==25 && a==word(f->memory,0x923)) f->memory[a]^=0x40;
    if (f->action==20 && a==0x3a0) f->memory[a]^=0xc0;
    if (f->action==21 && a==0x39e) f->pcm->runtime.transmission_service=false;
    if (f->action==22 && a>=0xf377 && a<=0xf37f) f->memory[a]^=0xff;
    if (f->action==23 && a==0x391) { f->pcm->serial.sessions=0;f->pcm->serial.service_expiry=1; }
    return PCM_OK;
}
static PcmStatus service_write8(void *v,uint16_t a,uint8_t value)
{
    Fixture *f=v;service_transfer(f->pcm,f,false);
    PcmStatus r=record(f,'W',8,a,value);if (r!=PCM_OK) return r;
    f->memory[a]=value;service_transfer(f->pcm,f,true);return PCM_OK;
}
static PcmStatus service_read16(void *v,uint16_t a,uint16_t *out)
{
    Fixture *f=v;service_transfer(f->pcm,f,false);return serial_read16(v,a,out);
}
static PcmStatus service_write16(void *v,uint16_t a,uint16_t value)
{
    Fixture *f=v;service_transfer(f->pcm,f,false);PcmStatus r=serial_write16(v,a,value);
    if (r==PCM_OK) service_transfer(f->pcm,f,true);
    return r;
}
static void service_init(Fixture *f,Pcm *pcm,PcmCalibration *root,PcmFuelCalibration *fuel,
                         PcmIacCalibration *iac,PcmAirCalibration *air,PcmIoCalibration *io,
                         PcmMixtureCalibration *mix,PcmFeedbackCalibration *fb,PcmDeliveryCalibration *dl)
{
    serial_init(f,pcm,root,fuel,iac,air,io,mix,fb,dl);
    f->platform.read8=service_read8;f->platform.write8=service_write8;
    f->platform.read16=service_read16;f->platform.write16=service_write16;
}
static PcmStatus service_prefix(Pcm *pcm,PcmTask task)
{
    Fixture *f=pcm->platform->context;CHECK(task==PCM_TRANSMISSION_INPUT_PREFIX);
    PcmStatus r=record(f,'T',0,0xae85,f->memory[0x921]);if (r!=PCM_OK) return r;
    if (f->action==24) pcm->serial.receive_age=199;
    return (PcmStatus)f->memory[0x921];
}
/* Supplied ordinary IRQ entry/return mask. The native target frame stays separate. */
static PcmStatus service_irq(Pcm *pcm,Fixture *f)
{
    bool previous=f->masked;f->masked=true;PcmStatus r=pcm_sci_irq(pcm);
    if (r==PCM_OK) f->masked=previous;
    return r;
}
static PcmStatus service_wire(Pcm *pcm,Fixture *f,bool split)
{
    unsigned n=word(f->memory,0x919),limit=word(f->memory,0x91c);
    if (n>255 || limit>512 || (split && n==0)) return PCM_BAD_CONFIGURATION;
    for (unsigned i=0;i<n;++i) {
        PcmStatus r;
        if (split && i+1==n) { r=pcm_serial_idle(pcm);if (r!=PCM_OK) return r; }
        f->memory[PCM_SCDR]=f->memory[0xa000+i];f->memory[PCM_SCSR]=f->memory[0xa100+i];
        r=service_irq(pcm,f);if (r!=PCM_OK) return r;
    }
    for (unsigned i=0;i<limit;++i) {
        uint8_t control=f->memory[PCM_SCCR2];if (control==0x26) break;
        f->memory[PCM_SCSR]=(control&0x80u)?0x80:0x40;
        PcmStatus r=service_irq(pcm,f);if (r!=PCM_OK) return r;
    }
    return PCM_OK;
}
static PcmStatus service_execute(unsigned mode,Pcm *pcm,Fixture *f,uint32_t *out)
{
    uint8_t byte;PcmStatus r;
#define RUN(call) do { r=(call);if (r!=PCM_OK) return r; } while (0)
    switch (mode) {
    case 0:RUN(pcm_diagnostic_checksum(pcm,&byte));*out=byte;return PCM_OK;
    case 1:return pcm_diagnostic_clear_engine(pcm);
    case 2:return pcm_diagnostic_clear_transmission(pcm);
    case 3:return pcm_service_status(pcm);
    case 4:return pcm_service_transmission(pcm);
    case 5:return pcm_service_engine(pcm);
    case 6:return pcm_service_clear(pcm);
    case 7:return pcm_service_cleanup(pcm);
    case 8:return pcm_serial_service(pcm);
    case 9:return pcm_serial_service_poll(pcm);
    case 10:return pcm_transmission_input(pcm);
    case 11:RUN(service_wire(pcm,f,false));return pcm_serial_service_poll(pcm);
    case 12:RUN(service_wire(pcm,f,false));RUN(pcm_serial_service(pcm));return pcm_spark_service(pcm);
    case 13:RUN(pcm_serial_service(pcm));return pcm_serial_service_poll(pcm);
    case 14:RUN(pcm_serial_service(pcm));RUN(pcm_serial_idle(pcm));RUN(pcm_serial_service(pcm));return pcm_spark_service(pcm);
    case 15:RUN(service_wire(pcm,f,false));RUN(pcm_serial_idle(pcm));RUN(service_wire(pcm,f,false));return pcm_serial_service(pcm);
    case 16:RUN(pcm_serial_idle(pcm));RUN(service_wire(pcm,f,false));return pcm_serial_service(pcm);
    case 17:RUN(pcm_serial_service(pcm));return pcm_spark_service(pcm);
    case 18:RUN(service_wire(pcm,f,true));return pcm_serial_service(pcm);
    case 19:RUN(pcm_serial_next(pcm,pcm->serial.descriptor,f->memory[0x918],&byte));*out=byte;return PCM_OK;
    default:return PCM_BAD_CONFIGURATION;
    }
#undef RUN
}
static void service_contracts(void)
{
    static Fixture f;Pcm pcm;PcmCalibration root;PcmFuelCalibration fuel;PcmIacCalibration iac;
    PcmAirCalibration air;PcmIoCalibration io;PcmMixtureCalibration mix;PcmFeedbackCalibration fb;PcmDeliveryCalibration dl;
#define INIT() service_init(&f,&pcm,&root,&fuel,&iac,&air,&io,&mix,&fb,&dl)
    INIT();CHECK(pcm_transmission_input(&pcm)==PCM_UNIMPLEMENTED && pcm.unresolved_task==PCM_TRANSMISSION_INPUT_PREFIX && f.used==0);
    INIT();f.platform.task[PCM_TRANSMISSION_INPUT_PREFIX]=service_prefix;f.memory[0x921]=PCM_TRAP_BOUNDARY;
    CHECK(pcm_transmission_input(&pcm)==PCM_TRAP_BOUNDARY && f.used==1);
    INIT();uint8_t value=99;f.fail_at=2;
    CHECK(pcm_diagnostic_checksum(&pcm,&value)==PCM_NO_HARDWARE && value==99);
    CHECK(pcm_diagnostic_checksum(&pcm,NULL)==PCM_BAD_CONFIGURATION);
    INIT();pcm.serial.clear_engine=true;f.fail_at=3;
    CHECK(pcm_service_clear(&pcm)==PCM_NO_HARDWARE && !(pcm.serial.clear_edges&0x80));
    INIT();pcm.serial.sessions=1;pcm.serial.engine_command=4;f.memory[0x391]=0x10;
    pcm.fuel.blm_cells[0]=7;CHECK(pcm_service_engine(&pcm)==PCM_OK && pcm.fuel.blm_cells[0]==128 && (pcm.serial.clear_edges&0x10));
    pcm.fuel.blm_cells[0]=7;CHECK(pcm_service_engine(&pcm)==PCM_OK && pcm.fuel.blm_cells[0]==7);
    pcm.serial.engine_command=1;f.memory[0x391]=0;CHECK(pcm_service_engine(&pcm)==PCM_OK && (pcm.serial.clear_edges&0x10));
    pcm.serial.engine_command=4;CHECK(pcm_service_engine(&pcm)==PCM_OK && !(pcm.serial.clear_edges&0x10));
    INIT();for (unsigned a=0xb;a<=0x34;++a) f.memory[a]=255;
    f.memory[0x25]=71;f.memory[0x2e]=72;f.memory[0x56]=73;
    service_transfer(&pcm,&f,true); /* Recovery counters now have canonical native owners. */
    CHECK(pcm_diagnostic_clear_transmission(&pcm)==PCM_OK && f.memory[0x25]==71 && f.memory[0x2e]==72 && f.memory[0x56]==73);
#undef INIT
    puts("Service prefix dependency, checksum/clear failed prefixes, qualified BLM rearm and diagnostic-clear holes pass.");
}
int main(int argc,char **argv)
{
    if (argc==2 && strcmp(argv[1],"--contracts")==0) { service_contracts();return 0; }
    static Fixture f;Pcm pcm;PcmCalibration root;PcmFuelCalibration fuel;PcmIacCalibration iac;
    PcmAirCalibration air;PcmIoCalibration io;PcmMixtureCalibration mix;PcmFeedbackCalibration fb;PcmDeliveryCalibration dl;PcmSparkCalibration spark;uint8_t curve[17];uint8_t backing[11][527],air_views[3][527],fb_views[2][527];
    if (argc==2) return inherited_serial_main(argc,argv);
    const char *rom_path=getenv("PCM_SERIAL_ROM");CHECK(rom_path!=NULL);
    FILE *rom_file=fopen(rom_path,"rb");CHECK(rom_file!=NULL);
    CHECK(fread(serial_rom,1,65536,rom_file)==65536);CHECK(fclose(rom_file)==0);serial_rom_loaded=true;
    uint16_t outputs[1536];unsigned output_count=0;bool selected[0x4000]={false};
    for (unsigned a=0x3000;a<0x3035;++a) selected[a]=true;
    for (unsigned a=0x3fc0;a<0x3ffe;++a) selected[a]=true;
    for (unsigned k=0;k<7;++k) {
        const Mapping *m=k==0?reference_state_map:k==1?fuel_state_map:k==2?air_state_map:k==3?mixture_state_map:k==4?feedback_state_map:k==5?delivery_state_map:serial_state_map;
        size_t count=k==0?SIZE(reference_state_map):k==1?SIZE(fuel_state_map):k==2?SIZE(air_state_map):k==3?SIZE(mixture_state_map):k==4?SIZE(feedback_state_map):k==5?SIZE(delivery_state_map):SIZE(serial_state_map);
        for (size_t i=0;i<count;++i) { for (unsigned j=0;j<m[i].count;++j) selected[m[i].address+j]=true;if (m[i].width==16) selected[m[i].address+1]=true; }
    }
    for (unsigned i=0;i<SIZE(service_state_map);++i)
        for (unsigned j=0;j<service_state_map[i].count;++j) selected[service_state_map[i].address+j]=true;
    for (unsigned a=0;a<0xa0;++a) selected[a]=true;
    for (unsigned a=0x182;a<0x186;++a) selected[a]=true;
    selected[0x817]=selected[0x21c]=selected[0x81c]=true;
    for (unsigned a=0x360;a<0x3b0;++a) selected[a]=true;
    selected[PCM_COPRST]=true;
    for (unsigned a=0;a<0x4000;++a) if (selected[a]) { CHECK(output_count<SIZE(outputs));outputs[output_count++]=(uint16_t)a; }
    unsigned mode,count;
    while (scanf("%u %u",&mode,&count)==2) {
        CHECK(mode<20 && count<4096);service_init(&f,&pcm,&root,&fuel,&iac,&air,&io,&mix,&fb,&dl);
        for (unsigned i=0;i<count;++i) { unsigned a,v;CHECK(scanf("%u %u",&a,&v)==2 && a<65536 && v<256);f.memory[a]=(uint8_t)v; }
        service_transfer(&pcm,&f,true);transfer(&root,f.memory,reference_cal_map,SIZE(reference_cal_map),true);
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
        spark=pcm_reference_spark_calibration;spark.missing_reference_age_cap=f.memory[0x4d96];root.spark=&spark;
        f.fail_at=word(f.memory,0x91e)?word(f.memory,0x91e):f.memory[0x907];f.action=f.memory[0x908];f.masked=f.memory[0x909]!=0;
        if (f.memory[0x920]) f.platform.task[PCM_TRANSMISSION_INPUT_PREFIX]=service_prefix;
        if (f.memory[0x913]) f.platform.task[PCM_AFR_EXTENSION]=mixture_extension;
        uint32_t value=0;PcmStatus status=service_execute(mode,&pcm,&f,&value);service_transfer(&pcm,&f,false);
        printf("{\"status\":%u,\"value\":%u,\"unresolved\":%u,\"masked\":%u,\"state\":[",(unsigned)status,(unsigned)value,(unsigned)(pcm.unresolved_task==PCM_TRANSMISSION_INPUT_PREFIX),(unsigned)f.masked);
        for (unsigned i=0;i<output_count;++i) printf("%s%u",i?",":"",f.memory[outputs[i]]);
        printf("],\"events\":[");
        for (unsigned i=0;i<f.used;++i) { Event *e=&f.events[i];printf("%s[\"%c\",%u,%u,%u,%u]",i?",":"",e->kind,e->width,e->address,e->value,(unsigned)e->masked); }
        puts("]}");
    }
    return 0;
}
