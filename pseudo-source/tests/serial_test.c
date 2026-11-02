#define PCM_DELIVERY_TEST_MAIN inherited_delivery_main
#include "fuel_delivery_test.c"
#undef PCM_DELIVERY_TEST_MAIN
#include "serial.h"
#include "startup.h"
#include "serial_fixture_map.h"

static uint8_t serial_rom[65536];static bool serial_rom_loaded;
static void serial_transfer(Pcm *pcm,Fixture *f,bool load)
{
    delivery_transfer(pcm,f,load);transfer(pcm,f->memory,serial_state_map,SIZE(serial_state_map),load);
}
/* This supplied test backend coherently binds the selected named Pcm fields.
 * It is an address-space fixture, not a proposed target ABI or RAM placement. */
static PcmStatus serial_read8(void *v,uint16_t a,uint8_t *out)
{
    Fixture *f=v;serial_transfer(f->pcm,f,false);uint8_t sample=f->memory[a];
    PcmStatus result=(a>=0x3000 && a<0x4000)?record(f,'R',8,a,sample):PCM_OK;
    if (result!=PCM_OK) return result;
    *out=sample;
    if (f->action==17 && a==PCM_SCCR2) { f->memory[a]^=0xe0;f->memory[PCM_SCSR]=0xe0; }
    return PCM_OK;
}
static PcmStatus serial_read16(void *v,uint16_t a,uint16_t *out)
{
    Fixture *f=v;serial_transfer(f->pcm,f,false);uint16_t sample=word(f->memory,a);
    PcmStatus result=(a>=0x3000 && a<0x4000)?record(f,'R',16,a,sample):PCM_OK;
    if (result!=PCM_OK) return result;
    *out=sample;
    if (f->action==19 && a==0x51bb) f->pcm->serial.service_age=65535;
    if (f->action==19 && a==0x51bd) f->pcm->serial.service_expiry=65535;
    if (f->action==15 && a==0x1f0) f->pcm->spark.command_latched+=0x0101;
    return PCM_OK;
}
static PcmStatus serial_write8(void *v,uint16_t a,uint8_t value)
{
    Fixture *f=v;serial_transfer(f->pcm,f,false);
    PcmStatus result=(a>=0x3000 && a<0x4000)?record(f,'W',8,a,value):PCM_OK;
    if (result!=PCM_OK) return result;
    f->memory[a]=value;serial_transfer(f->pcm,f,true);
    if (a==PCM_SCDR && f->action==13) { f->pcm->serial.checksum=7;f->pcm->serial.count=254; }
    if (a==PCM_SCDR && f->action==14) { f->pcm->spark.command_latched+=0x0101;++f->pcm->reference.battery; }
    return PCM_OK;
}
static PcmStatus serial_write16(void *v,uint16_t a,uint16_t value)
{
    Fixture *f=v;serial_transfer(f->pcm,f,false);
    PcmStatus result=(a>=0x3000 && a<0x4000)?record(f,'W',16,a,value):PCM_OK;
    if (result!=PCM_OK) return result;
    f->memory[a]=(uint8_t)(value>>8);f->memory[(uint16_t)(a+1u)]=(uint8_t)value;
    serial_transfer(f->pcm,f,true);return PCM_OK;
}
static PcmStatus serial_mask(void *v,bool masked)
{
    Fixture *f=v;PcmStatus result=delivery_mask(v,masked);if (result!=PCM_OK) return result;
    if (f->action==18) {
        if (masked) { f->pcm->serial.length=0;f->pcm->serial.descriptor=0xa300; }
        else f->pcm->runtime.engine_service=true;
    }
    return PCM_OK;
}
static PcmStatus serial_delay(void *v,uint16_t cycles)
{
    Fixture *f=v;PcmStatus result=delivery_delay(v,cycles);if (result!=PCM_OK) return result;
    if (cycles==11 && f->action==16) f->memory[PCM_BOARD_CONTROL]^=4;
    return PCM_OK;
}
static void serial_init(Fixture *f,Pcm *pcm,PcmCalibration *root,PcmFuelCalibration *fuel,
                         PcmIacCalibration *iac,PcmAirCalibration *air,PcmIoCalibration *io,
                         PcmMixtureCalibration *mix,PcmFeedbackCalibration *fb,PcmDeliveryCalibration *dl)
{
    delivery_init(f,pcm,root,fuel,iac,air,io,mix,fb,dl);
    if (serial_rom_loaded) memcpy(f->memory+0x4000,serial_rom+0x4000,0xc000);
    f->platform.read8=serial_read8;f->platform.read16=serial_read16;
    f->platform.write8=serial_write8;f->platform.write16=serial_write16;
    f->platform.mask_irq=serial_mask;f->platform.delay_cycles=serial_delay;
}
static PcmStatus serial_drain(Fixture *f,Pcm *pcm,unsigned limit)
{
    for (unsigned i=0;i<limit;++i) {
        uint8_t control=f->memory[PCM_SCCR2];
        if (control==0x26) break;
        f->memory[PCM_SCSR]=(control&0x80)?0x80:0x40;
        PcmStatus result=pcm_sci_irq(pcm);if (result!=PCM_OK) return result;
    }
    return PCM_OK;
}
static PcmStatus serial_execute(unsigned mode,Pcm *pcm,Fixture *f,uint32_t *value)
{
    PcmStatus result;uint16_t descriptor;uint8_t byte;
#define RUN(call) do { result=(call);if (result!=PCM_OK) return result; } while (0)
    switch (mode) {
    case 0:return pcm_serial_receive(pcm);
    case 1:return pcm_serial_transmit(pcm);
    case 2:return pcm_sci_irq(pcm);
    case 3:return pcm_serial_poll(pcm);
    case 4:return pcm_serial_idle(pcm);
    case 5:return pcm_serial_abort(pcm);
    case 6:return pcm_serial_start(pcm,pcm->serial.descriptor);
    case 7:return pcm_serial_send(pcm,f->memory[0x917]);
    case 8:return pcm_serial_finish(pcm);
    case 9:return pcm_serial_payload(pcm,pcm->serial.descriptor,f->memory[0x918],f->memory[0x917]);
    case 10:return pcm_serial_accept(pcm,pcm->serial.descriptor);
    case 11:RUN(pcm_serial_find(pcm,f->memory[0x917],&descriptor));*value=descriptor;return PCM_OK;
    case 12:RUN(pcm_serial_next(pcm,pcm->serial.descriptor,f->memory[0x918],&byte));*value=byte;return PCM_OK;
    case 13:return pcm_serial_driver(pcm,f->memory[0x917]!=0);
    case 14:RUN(pcm_serial_clear_ram(pcm));*value=f->memory[0x3ff];return PCM_OK;
    case 15:return pcm_reset_serial(pcm);
    case 16:case 18:
        if (word(f->memory,0x919)>255 || word(f->memory,0x91c)>512) return PCM_BAD_CONFIGURATION;
        for (unsigned i=0;i<word(f->memory,0x919);++i) {
            f->memory[PCM_SCDR]=f->memory[0xa000+i];f->memory[PCM_SCSR]=f->memory[0xa100+i];
            RUN(mode==18?pcm_sci_irq(pcm):pcm_serial_receive(pcm));
        }
        if (mode==18) return serial_drain(f,pcm,word(f->memory,0x91c));
        return PCM_OK;
    case 17:if (word(f->memory,0x91c)>512) return PCM_BAD_CONFIGURATION;
        return serial_drain(f,pcm,word(f->memory,0x91c));
    case 19:RUN(pcm_serial_idle(pcm));return pcm_serial_poll(pcm);
    default:return PCM_BAD_CONFIGURATION;
    }
#undef RUN
}
static void serial_contracts(void)
{
    static Fixture f;Pcm pcm;PcmCalibration root;PcmFuelCalibration fuel;PcmIacCalibration iac;
    PcmAirCalibration air;PcmIoCalibration io;PcmMixtureCalibration mix;PcmFeedbackCalibration fb;PcmDeliveryCalibration dl;
#define INIT() serial_init(&f,&pcm,&root,&fuel,&iac,&air,&io,&mix,&fb,&dl)
    INIT();pcm.serial.count=255;pcm.serial.checksum=2;f.fail_at=1;
    CHECK(pcm_serial_send(&pcm,3)==PCM_NO_HARDWARE && pcm.serial.count==255 && pcm.serial.checksum==2);
    INIT();pcm.serial.sessions=0x85;pcm.serial.last_id=0xf4;pcm.serial.receive[0]=4;f.fail_at=1;
    CHECK(pcm_serial_abort(&pcm)==PCM_NO_HARDWARE && pcm.serial.sessions==0x85 && pcm.serial.last_id==0xf4 && pcm.serial.receive[0]==4 && pcm.serial.descriptor==0);
    INIT();pcm.serial.receive_age=77;pcm.serial.checksum=99;f.fail_at=2;
    CHECK(pcm_serial_receive(&pcm)==PCM_NO_HARDWARE && pcm.serial.receive_age==77 && pcm.serial.checksum==99);
    INIT();f.memory[PCM_SCSR]=0x0e;pcm.serial.count=4;pcm.serial.receive_age=77;
    CHECK(pcm_serial_receive(&pcm)==PCM_OK && pcm.serial.receive_age==0 && pcm.serial.count==0 && f.memory[PCM_SCCR2]==0x26);
    INIT();pcm.serial.sessions=1;pcm.serial.receive_age=199;pcm.serial.busy=true;pcm.serial.engine_command=4;pcm.serial.receive[5]=55;f.fail_at=2;
    CHECK(pcm_serial_idle(&pcm)==PCM_NO_HARDWARE && f.masked && !pcm.serial.busy && pcm.serial.sessions==0 && pcm.serial.engine_command==0 && pcm.serial.receive[5]==55);
    INIT();f.memory[PCM_BOARD_CONTROL]=4;f.memory[PCM_BOARD_CONTROL+1]=0;CHECK(pcm_serial_driver(&pcm,true)==PCM_OK && word(f.memory,PCM_BOARD_CONTROL)==0x0404);
    CHECK(pcm_serial_driver(&pcm,false)==PCM_OK && word(f.memory,PCM_BOARD_CONTROL)==0x0400);
    INIT();for (unsigned a=0x360;a<0x400;++a) f.memory[a]=0xaa;serial_transfer(&pcm,&f,true);
    CHECK(pcm_serial_clear_ram(&pcm)==PCM_OK && f.memory[0x3ff]==0xaa);
    serial_transfer(&pcm,&f,false);for (unsigned a=0x360;a<0x3ff;++a) CHECK(f.memory[a]==0);
    INIT();pcm.serial.sessions=1;f.platform.read16=NULL;CHECK(pcm_serial_poll(&pcm)==PCM_OK && f.used==0);
    INIT();uint16_t out;CHECK(pcm_serial_memory_read16(&pcm,0x362,&out)==PCM_OK && out==0);
    CHECK(pcm_serial_find(&pcm,0xf4,NULL)==PCM_BAD_CONFIGURATION);
    INIT();f.memory[0x51bf]=0x51;f.memory[0x51c0]=0xbf;f.memory[0x51c1]=0xaa;out=0xbeef;
    CHECK(pcm_serial_find(&pcm,0xbb,&out)==PCM_BAD_CONFIGURATION && out==0xbeef && f.used==0);
    INIT();f.platform.read8=NULL;f.platform.read16=NULL;f.platform.write8=NULL;
    CHECK(pcm_serial_memory_write8(&pcm,0x362,0x12)==PCM_OK);
    CHECK(pcm_serial_memory_write8(&pcm,0x363,0x34)==PCM_OK);
    CHECK(pcm_serial_memory_read16(&pcm,0x362,&out)==PCM_OK && out==0x1234);
    CHECK(pcm_serial_memory_read16(&pcm,0x4000,&out)==PCM_NO_HARDWARE);
    CHECK(pcm_serial_memory_write8(&pcm,0x38f,1)==PCM_NO_HARDWARE);
    CHECK(pcm_serial_memory_read8(&pcm,0x360,NULL)==PCM_BAD_CONFIGURATION);
    CHECK(pcm_serial_memory_read16(&pcm,0x360,NULL)==PCM_BAD_CONFIGURATION);
#undef INIT
    puts("SCI prefix failures, partial abort retention, idle expiry, serial RAM ownership,03FF retention and SCI/fuel driver-bit isolation pass.");
}
#ifndef PCM_SERIAL_TEST_MAIN
#define PCM_SERIAL_TEST_MAIN main
#endif
int PCM_SERIAL_TEST_MAIN(int argc,char **argv)
{
    if (argc==2 && strcmp(argv[1],"--contracts")==0) { serial_contracts();return 0; }
    static Fixture f;Pcm pcm;PcmCalibration root;PcmFuelCalibration fuel;PcmIacCalibration iac;
    PcmAirCalibration air;PcmIoCalibration io;PcmMixtureCalibration mix;PcmFeedbackCalibration fb;PcmDeliveryCalibration dl;PcmSparkCalibration spark;uint8_t curve[17];uint8_t backing[11][527],air_views[3][527],fb_views[2][527];
    if (argc==2) return inherited_delivery_main(argc,argv);
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
    for (unsigned a=0x360;a<0x3b0;++a) selected[a]=true;
    for (unsigned a=0xa00;a<0xd00;++a) selected[a]=true;
    selected[PCM_COPRST]=true;
    for (unsigned a=0;a<0x4000;++a) if (selected[a]) { CHECK(output_count<SIZE(outputs));outputs[output_count++]=(uint16_t)a; }
    unsigned mode,count;
    while (scanf("%u %u",&mode,&count)==2) {
        CHECK(mode<20 && count<4096);serial_init(&f,&pcm,&root,&fuel,&iac,&air,&io,&mix,&fb,&dl);
        for (unsigned i=0;i<count;++i) { unsigned a,v;CHECK(scanf("%u %u",&a,&v)==2 && a<65536 && v<256);f.memory[a]=(uint8_t)v; }
        serial_transfer(&pcm,&f,true);transfer(&root,f.memory,reference_cal_map,SIZE(reference_cal_map),true);
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
        if (f.memory[0x913]) f.platform.task[PCM_AFR_EXTENSION]=mixture_extension;
        uint32_t value=0;PcmStatus status=serial_execute(mode,&pcm,&f,&value);serial_transfer(&pcm,&f,false);
        printf("{\"status\":%u,\"value\":%u,\"unresolved\":%u,\"masked\":%u,\"state\":[",(unsigned)status,(unsigned)value,(unsigned)(pcm.unresolved_task==PCM_AFR_EXTENSION),(unsigned)f.masked);
        for (unsigned i=0;i<output_count;++i) printf("%s%u",i?",":"",f.memory[outputs[i]]);
        printf("],\"events\":[");
        for (unsigned i=0;i<f.used;++i) { Event *e=&f.events[i];printf("%s[\"%c\",%u,%u,%u,%u]",i?",":"",e->kind,e->width,e->address,e->value,(unsigned)e->masked); }
        puts("]}");
    }
    return 0;
}
