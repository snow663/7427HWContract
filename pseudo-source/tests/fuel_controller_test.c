#define PCM_DELIVERY_TEST_MAIN inherited_delivery_main
#include "fuel_delivery_test.c"
#undef PCM_DELIVERY_TEST_MAIN
#include "control.h"

#define B(a,m) {a,8,0,1,offsetof(Pcm,m)}
#define W(a,m) {a,16,0,1,offsetof(Pcm,m)}
#define F(a,b,m) {a,0,b,1,offsetof(Pcm,m)}
static const Mapping controller_state_map[]={
    F(0x4f,0x80,runtime.spark_running),F(0x51,8,runtime.ignition_off),F(0x44,8,spark.first_reference),
    B(0x89,transmission.range_context),F(0x47,1,io.map_transient),B(0x1c5,io.map_hold),
    B(0x80c,io.vss_changes),W(0x80d,io.vss_timestamp),W(0x80f,io.vss_previous),B(0x811,io.vss_age),
    W(0x28e,spark.rpm_monitor_filtered),B(0x28d,spark.rpm_monitor_delta),
};
#undef B
#undef W
#undef F
static void controller_transfer(Fixture *f,bool load)
{
    Pcm *pcm=f->pcm;delivery_transfer(pcm,f,load);
    transfer(pcm,f->memory,controller_state_map,SIZE(controller_state_map),load);
    if (load) pcm->io.map_context=f->memory[0x47]&0xfeu;
    else f->memory[0x47]=(uint8_t)((f->memory[0x47]&1u)|(pcm->io.map_context&0xfeu));
    if (f->extra_transfer!=NULL) f->extra_transfer(pcm,f->memory,load);
}
static PcmStatus controller_read8(void *v,uint16_t a,uint8_t *out)
{
    Fixture *f=v;controller_transfer(f,false);PcmStatus status=read8(v,a,out);
    if (status!=PCM_OK) return status;
    controller_transfer(f,false);
    if (f->action==30 && a==0x75) f->memory[a]^=0xd7;
    if (f->action==31 && (a==0x50e2 || a==0x50e3)) f->memory[a]=(uint8_t)(*out+17u);
    if (f->action==33 && a==0x28e) f->memory[a]=(uint8_t)(*out+17u);
    if (f->action==36 && a==0x29a) f->memory[a]=(uint8_t)(*out+17u);
    controller_transfer(f,true);return PCM_OK;
}
static PcmStatus controller_read16(void *v,uint16_t a,uint16_t *out)
{
    Fixture *f=v;controller_transfer(f,false);PcmStatus status=delivery_read16(v,a,out);
    if (status!=PCM_OK) return status;
    controller_transfer(f,false);
    if (f->action==32 && a>=0x50e8 && a<0x5200) f->memory[a]=(uint8_t)(f->memory[a]+11u);
    if (f->action==35 && a==0x27e) { f->memory[a]=0xde;f->memory[a+1]=0xad; }
    if (f->action==37 && a==PCM_EST_COUNTER) f->memory[2]^=4;
    controller_transfer(f,true);return PCM_OK;
}
static PcmStatus controller_write8(void *v,uint16_t a,uint8_t value)
{
    Fixture *f=v;controller_transfer(f,false);PcmStatus status=write8(v,a,value);
    if (status==PCM_OK) controller_transfer(f,true);
    return status;
}
static PcmStatus controller_write16(void *v,uint16_t a,uint16_t value)
{
    Fixture *f=v;controller_transfer(f,false);PcmStatus status=write16(v,a,value);
    if (status!=PCM_OK) return status;
    controller_transfer(f,true);
    if (f->action==12 && a==PCM_INJECTOR_WORD && value==0) f->pcm->io.coolant_context^=0x10;
    controller_transfer(f,false);
    if (f->action==34 && a==0x28a) f->memory[a]^=0x55;
    controller_transfer(f,true);return PCM_OK;
}
static PcmStatus controller_mask(void *v,bool masked)
{
    Fixture *f=v;controller_transfer(f,false);PcmStatus status=delivery_mask(v,masked);
    if (status==PCM_OK) { if (f->action==38 && !masked) f->pcm->scheduler.phase^=6;controller_transfer(f,false); }
    return status;
}
static PcmStatus controller_delay(void *v,uint16_t cycles)
{
    Fixture *f=v;controller_transfer(f,false);PcmStatus status=delivery_delay(v,cycles);
    if (status==PCM_OK) controller_transfer(f,false);
    return status;
}
static PcmStatus governor_extension(Pcm *pcm,PcmTask task)
{
    Fixture *f=pcm->application;CHECK(task==PCM_GOVERNOR_EXTENSION);controller_transfer(f,false);
    PcmStatus status=record(f,'T',0,0x1809,pcm->governor.extension_value);if (status!=PCM_OK) return status;
    pcm->governor.extension_value=f->memory[0x921];pcm->governor.extension_carry=(f->memory[0x922]&1u)!=0;
    return (PcmStatus)f->memory[0x923];
}
typedef struct {
    PcmCalibration root;PcmFuelCalibration fuel;PcmIacCalibration iac;PcmAirCalibration air;
    PcmIoCalibration io;PcmMixtureCalibration mix;PcmFeedbackCalibration feedback;PcmDeliveryCalibration delivery;
} Profiles;
static uint8_t stock[65536];
static void controller_init(Fixture *f,Pcm *pcm,Profiles *p)
{
    delivery_init(f,pcm,&p->root,&p->fuel,&p->iac,&p->air,&p->io,&p->mix,&p->feedback,&p->delivery);
    memcpy(f->memory+0x4000,stock+0x4000,0xc000);
    f->platform.read8=controller_read8;f->platform.read16=controller_read16;
    f->platform.write8=controller_write8;f->platform.write16=controller_write16;
    f->platform.mask_irq=controller_mask;f->platform.delay_cycles=controller_delay;
}
static void controller_profile(Fixture *f,Profiles *p)
{
    transfer(&p->root,f->memory,reference_cal_map,SIZE(reference_cal_map),true);
    transfer(&p->fuel,f->memory,fuel_cal_map,SIZE(fuel_cal_map),true);
    transfer(&p->air,f->memory,air_cal_map,SIZE(air_cal_map),true);
    transfer(&p->mix,f->memory,mixture_cal_map,SIZE(mixture_cal_map),true);
    transfer(&p->feedback,f->memory,feedback_cal_map,SIZE(feedback_cal_map),true);
    transfer(&p->delivery,f->memory,delivery_cal_map,SIZE(delivery_cal_map),true);
    p->root.mode_d=f->memory[0x400d];p->root.mode_f=f->memory[0x400f];
    p->io.map_hold_reload=f->memory[0x4139];p->io.map_rpm_delta_limit=f->memory[0x413a];
    p->iac.step_battery_minimum=f->memory[0x4eb6];
    for (size_t i=0;i<SIZE(air_tables);++i) {
        const AirTableMapping *m=&air_tables[i];PcmTable2D *t=(PcmTable2D *)(void *)((uint8_t *)&p->air+m->offset);
        *t=(PcmTable2D){f->memory[m->address],f->memory[m->address+1],f->memory[m->address+2],527,f->memory+m->address+3};
    }
    for (size_t i=0;i<SIZE(feedback_tables);++i) {
        const AirTableMapping *m=&feedback_tables[i];PcmTable2D *t=(PcmTable2D *)(void *)((uint8_t *)&p->feedback+m->offset);
        *t=(PcmTable2D){f->memory[m->address],f->memory[m->address+1],f->memory[m->address+2],527,f->memory+m->address+3};
    }
    for (size_t i=0;i<SIZE(mixture_tables);++i) {
        const MixtureTable *m=&mixture_tables[i];uint8_t *ptr=(uint8_t *)&p->mix+m->offset;
        if (m->kind==0) *(PcmScaledCurve *)(void *)ptr=(PcmScaledCurve){256,f->memory[m->address],f->memory+m->address+1};
        else if (m->kind==1) *(PcmCappedCurve *)(void *)ptr=(PcmCappedCurve){f->memory[m->address],0,f->memory+m->address+1};
        else *(PcmTable2D *)(void *)ptr=(PcmTable2D){f->memory[m->address],f->memory[m->address+1],f->memory[m->address+2],527,f->memory+m->address+3};
    }
    /* Capped-curve length is an 8-bit field; the existing stock bounded views
     * retain their declared lengths, with live ROM backing for neighboring reads. */
    for (size_t i=0;i<SIZE(mixture_tables);++i) if (mixture_tables[i].kind==1) {
        PcmCappedCurve *t=(PcmCappedCurve *)(void *)((uint8_t *)&p->mix+mixture_tables[i].offset);
        t->length=mixture_tables[i].capacity;
    }
    p->delivery.decel_throttle.limit=f->memory[0x4c94];p->delivery.decel_throttle.length=17;
    p->delivery.decel_throttle.values=f->memory+0x4c95;
}
static PcmStatus controller_execute(unsigned mode,Pcm *pcm)
{
    PcmStatus status;
    switch (mode) {
    case 0:return pcm_fuel_ignition(pcm);
    case 1:return pcm_governor_target(pcm);
    case 2:return pcm_governor_actuator(pcm);
    case 3:return pcm_fuel_inputs(pcm);
    case 4:return pcm_fuel_schedule(pcm);
    case 5:return pcm_fuel_control(pcm);
    case 6:status=pcm_fuel_control(pcm);return status==PCM_OK?pcm_reference_event(pcm):status;
    case 7:status=pcm_fuel_schedule(pcm);return status==PCM_OK?pcm_fuel_control(pcm):status;
    default:status=pcm_fuel_inputs(pcm);return status==PCM_OK?pcm_fuel_calculate(pcm):status;
    }
}
static void controller_contracts(void)
{
    static Fixture f;Pcm pcm;Profiles p;
    controller_init(&f,&pcm,&p);f.memory[0x27f]=8;f.memory[0x4009]=0;f.memory[0x400a]=8;
    f.memory[0x44]=0x10;controller_transfer(&f,true);
    CHECK(pcm_fuel_ignition(&pcm)==PCM_STOP_BOUNDARY && word(f.memory,0x27e)==8 && f.memory[0x3039]==8);
    CHECK(!pcm.runtime.fuel_running && !pcm.runtime.spark_running && pcm.runtime.ignition_off);
    CHECK(f.used>0 && f.events[f.used-1].address==0x3039);
    controller_init(&f,&pcm,&p);f.memory[0x400f]=1;f.memory[0x4f]=0x80;f.memory[0x86]=0x40;
    controller_transfer(&f,true);CHECK(pcm_governor_target(&pcm)==PCM_UNIMPLEMENTED && pcm.unresolved_task==PCM_GOVERNOR_EXTENSION);
    controller_init(&f,&pcm,&p);f.memory[0x299]=255;f.memory[0x288]=0xff;f.memory[0x289]=0xff;
    f.memory[0x50ff]=f.memory[0x5109]=0;f.memory[0x5100]=f.memory[0x5101]=0;
    f.memory[0x510a]=f.memory[0x510b]=0;controller_transfer(&f,true);
    CHECK(pcm_governor_actuator(&pcm)==PCM_OK && word(f.memory,0x288)==0 && word(f.memory,0x306c)==0x1fff);
    puts("Ignition STOP prefix, missing1809 and target-FF post-command integral clearing contracts pass.");
}
#ifndef PCM_CONTROLLER_TEST_MAIN
#define PCM_CONTROLLER_TEST_MAIN main
#endif
int PCM_CONTROLLER_TEST_MAIN(int argc,char **argv)
{
    const char *path=getenv("PCM_FUEL_CONTROLLER_ROM");CHECK(path!=NULL || argc==2);
    if (path!=NULL) { FILE *file=fopen(path,"rb");CHECK(file!=NULL && fread(stock,1,sizeof(stock),file)==sizeof(stock));CHECK(fclose(file)==0); }
    if (argc==2 && strcmp(argv[1],"--contracts")==0) { controller_contracts();return 0; }
    if (argc==2) return inherited_delivery_main(argc,argv);
    static Fixture f;Pcm pcm;Profiles p;unsigned mode,fail,action,masked,count;
    while (scanf("%u %u %u %u %u",&mode,&fail,&action,&masked,&count)==5) {
        CHECK(mode<9 && count<4096);controller_init(&f,&pcm,&p);
        for (unsigned i=0;i<count;++i) { unsigned a,value;CHECK(scanf("%u %u",&a,&value)==2 && a<65536 && value<256);f.memory[a]=(uint8_t)value; }
        controller_profile(&f,&p);controller_transfer(&f,true);f.fail_at=fail;f.action=action;f.masked=masked!=0;
        if (f.memory[0x913]) f.platform.task[PCM_AFR_EXTENSION]=mixture_extension;
        if (f.memory[0x920]) f.platform.task[PCM_GOVERNOR_EXTENSION]=governor_extension;
        PcmStatus status=controller_execute(mode,&pcm);controller_transfer(&f,false);
        unsigned unresolved=pcm.unresolved_task==PCM_AFR_EXTENSION?1:pcm.unresolved_task==PCM_GOVERNOR_EXTENSION?2:0;
        printf("{\"status\":%u,\"value\":0,\"unresolved\":%u,\"masked\":%u,\"state\":\"",(unsigned)status,unresolved,(unsigned)f.masked);
        for (unsigned a=0;a<0x900;++a) printf("%02x",(a>=0x3b0 && a<0x400) || (a>=0xad && a<=0xb2)?0:f.memory[a]);
        for (unsigned a=0x3000;a<0x3070;++a) printf("%02x",f.memory[a]);
        for (unsigned a=0x3fc0;a<0x3ffe;++a) printf("%02x",f.memory[a]);
        printf("\",\"events\":[");
        for (unsigned i=0;i<f.used;++i) { Event *e=&f.events[i];printf("%s[\"%c\",%u,%u,%u,%u]",i?",":"",e->kind,e->width,e->address,e->value,(unsigned)e->masked); }
        puts("]}");
    }
    return 0;
}
