#define PCM_BOOT_FIXTURE_ENTRY inherited_boot_main
#include "boot_system_test.c"
#undef PCM_BOOT_FIXTURE_ENTRY
#include "board_io.h"
#include "control.h"
#include "iac.h"

#define B(a,m) {a,8,0,1,offsetof(Pcm,m)}
#define W(a,m) {a,16,0,1,offsetof(Pcm,m)}
#define F(a,b,m) {a,0,b,1,offsetof(Pcm,m)}
/* Only native owners used at this joined boot entry, not a target RAM layout. */
static const Mapping controller_state_map[]={
 B(0x16,runtime.primary_faults),F(0x43,0x80,runtime.first_conversion),B(0x4e,io.auxiliary_output),
 W(0xfd,scheduler.run_counter),B(0x82d,io.raw_coolant),B(0xa8,io.coolant_conversion),
 B(0x283,iac.coolant_index),F(0x3f,0x40,iac.startup_cancel),B(0x842,knock.burst_gain),
 B(0x1e5,io.environmental_trim),B(0x243,io.environmental_factor),B(0x272,io.environmental_load),
 B(0x1cb,io.environmental_idle),B(0x1bb,io.environmental_density),F(0x41,2,spark.mat_negative),
 B(0x22f,spark.mat_sample),B(0x1fa,spark.mat_magnitude),B(0x1c9,spark.vacuum),
 B(0x1fc,spark.pe_advance),B(0x278,spark.pe_fraction),F(0x3d,0x20,runtime.power_enrichment),
 F(0x19,0x10,knock.sensor_fault),B(0x841,knock.octane_rpm_factor),B(0x843,knock.event_gain),
 B(0x844,knock.retard_limit),B(0x6f,spark.load_status),
 B(0x2b1,iac.baseline_on),B(0x29f,iac.bank[0].no_ac_snapshot),B(0x2a2,iac.bank[0].ac_snapshot),
 B(0x2a9,iac.bank[1].no_ac_snapshot),B(0x2ac,iac.bank[1].ac_snapshot),
 W(0x29d,iac.bank[0].no_ac),W(0x2a0,iac.bank[0].ac),W(0x2a7,iac.bank[1].no_ac),W(0x2aa,iac.bank[1].ac),
 B(0x37,iac.kicker_flags),B(0x88d,iac.kicker_timer),F(0x4b,0x80,iac.kicker_request),
 {0x36,7,0xdf,1,offsetof(Pcm,iac.context)},
 B(0xa6,fuel.raw_throttle),B(0x1a6,fuel.normalized_throttle),B(0x1c6,spark.map_filtered),
 W(0x1c3,io.map_filter),B(0x1c0,spark.load_coordinate),W(0x1c7,fuel.map_history),
 B(0x2f3,io.barometric_sample),B(0x2f4,spark.barometric_high),B(0x2f5,io.barometric_fraction),
 B(0x1cc,spark.barometric_pressure),B(0x1e4,io.tps_ae_factor),B(0x1e3,io.pe_throttle_threshold),
 B(0x1cd,io.pe_rpm_threshold),B(0x1ce,spark.normalized_load_divisor),
 B(0x282,iac.starting_coolant),B(0x885,iac.follower_closed_threshold),B(0x4c,transmission.output_shadow),
 B(0xd9,transmission.selected_gear),B(0x1d5,fuel.raw_oxygen),W(0x1d2,fuel.oxygen_filtered),
 W(0x1dc,fuel.tps_history),B(0x1da,spark.previous_throttle),B(0x1db,fuel.pe_previous_throttle),
 W(0x1de,fuel.throttle_decel_filter),B(0x1a1,io.auxiliary_sample),W(0x205,spark.bypass_baseline),
 W(0x851,fuel.authorization_capture),B(0x24a,fuel.commanded_afr),F(0x1a,2,runtime.adc_timeout),
 F(0x98,1,fuel.throttle_fault),F(4,8,spark.run_transition)
};
#undef B
#undef W
#undef F
static void controller_transfer(Pcm *pcm,uint8_t *memory,bool load)
{
    for (unsigned i=0;i<SIZE(controller_state_map);++i) {
        const Mapping *m=&controller_state_map[i];
        if (m->width==7) {
            volatile uint8_t *field=(volatile uint8_t *)(void *)((uint8_t *)pcm+m->offset);
            if (load) *field=memory[m->address]&m->mask;
            else memory[m->address]=(uint8_t)((memory[m->address]&~m->mask)|(*field&m->mask));
        } else transfer(pcm,memory,m,1,load);
    }
}
static PcmStatus controller_read8(void *v,uint16_t address,uint8_t *out)
{
    BootFixture *f=v;uint8_t saved=f->memory[address];
    if (address==PCM_ADCTL) f->memory[address]=(uint8_t)((saved&0x7f)|(f->polls>=f->memory[0x900]?0x80:0));
    PcmStatus r=boot_read8(v,address,out);
    if (address==PCM_ADCTL) { f->memory[address]=saved;if (r==PCM_OK) ++f->polls; }
    if (r==PCM_OK) {
        if (f->action==20 && address==PCM_PORTD) f->memory[address]^=0xc7;
        if (f->action==21 && (address==0x5b25 || address==0x48a8)) f->memory[address]=(uint8_t)(*out+37u);
        if (f->action==22 && address==0x1cc) {
            f->memory[address]=(uint8_t)(*out+17u);boot_transfer(f,true);
        }
    }
    return r;
}
static PcmStatus controller_write8(void *v,uint16_t address,uint8_t value)
{
    BootFixture *f=v;PcmStatus r=boot_write8(v,address,value);
    if (r==PCM_OK && address==PCM_ADCTL) f->polls=0;
    return r;
}
static PcmStatus controller_mask(void *v,bool masked)
{
    BootFixture *f=v;PcmStatus r=boot_record(f,'M',0,0,masked);
    if (r==PCM_OK) f->masked=masked;
    return r;
}
static PcmStatus controller_execute(unsigned mode,Pcm *pcm)
{
    switch (mode) {
    case 0:return pcm_baro_seed(pcm);
    case 1:return pcm_iac_restore(pcm);
    case 2:return pcm_iac_step_disable(pcm);
    case 3:return pcm_iac_boot(pcm);
    case 4:return pcm_transmission_throttle(pcm);
    case 5:return pcm_egr_feedback(pcm);
    case 6:return pcm_controller_baselines(pcm);
    case 7:return pcm_reset_controllers(pcm);
    default:return PCM_BAD_CONFIGURATION;
    }
}
int main(int argc,char **argv)
{
    const char *path=getenv("PCM_BOOT_ROM");CHECK(path!=NULL || argc==2);
    if (path!=NULL) {
        FILE *file=fopen(path,"rb");CHECK(file!=NULL && fread(boot_rom,1,65536,file)==65536);CHECK(fclose(file)==0);
    }
    CHECK(argc==1 || (argc==2 && strcmp(argv[1],"--contracts")==0));
    static BootFixture f;Pcm pcm;unsigned mode,fail,action,masked,count;
    PcmCalibration cal;PcmAirCalibration air;PcmIacCalibration iac;
    bool contracts=argc==2;
    while (contracts || scanf("%u %u %u %u %u",&mode,&fail,&action,&masked,&count)==5) {
        boot_init(&f,&pcm);f.extra_transfer=controller_transfer;f.platform.read8=controller_read8;
        f.platform.write8=controller_write8;f.platform.mask_irq=controller_mask;
        cal=pcm_reference_scheduler_calibration;air=pcm_reference_air_calibration;iac=pcm_reference_iac_calibration;
        cal.air=&air;cal.iac=&iac;pcm.calibration=&cal;
        if (contracts) {
            pcm.iac.state_flags=0;pcm.iac.step_control=255;
            CHECK(pcm_iac_step_disable(&pcm)==PCM_OK && pcm.iac.step_control==12);
            f.platform.delay_cycles=NULL;CHECK(pcm_controller_baselines(&pcm)==PCM_NO_HARDWARE);
            CHECK(word(f.memory,0x3fcc)==0xd000 && word(f.memory,0x3fea)==0);
            puts("IAC coil retention and ordered board-baseline failure contracts pass.");return 0;
        }
        CHECK(mode<8 && count<4096);
        for (unsigned i=0;i<count;++i) { unsigned a,v;CHECK(scanf("%u %u",&a,&v)==2 && a<65536 && v<256);f.memory[a]=(uint8_t)v; }
        /* Existing callable profiles are loaded where these focused cases vary them. */
        memcpy(air.coolant_table,f.memory+0xfc45,512);air.throttle_zero_minimum=f.memory[0x5b24];air.throttle_zero_gain=f.memory[0x5b27];
        iac.default_integral[0]=f.memory[0x4eb1];iac.default_integral[1]=f.memory[0x4eb2];
        iac.default_ac_warm=f.memory[0x4eb3];iac.default_ac_cold=f.memory[0x4eb4];iac.default_coolant=f.memory[0x4eb5];
        iac.default_baseline=f.memory[0x50d4];
        boot_transfer(&f,true);f.fail=fail;f.action=action;f.masked=masked!=0;
        PcmStatus status=controller_execute(mode,&pcm);boot_transfer(&f,false);
        printf("{\"status\":%u,\"value\":0,\"state\":\"",(unsigned)status);
        for (unsigned a=0;a<0x900;++a) printf("%02x",a>=0x3b0 && a<0x400?0:f.memory[a]);
        hex(f.memory,0x3000,0x3070);hex(f.memory,0x3fc0,0x3ffe);printf("\",\"events\":[");
        for (unsigned i=0;i<f.used;++i) { BootEvent *e=&f.events[i];printf("%s[\"%c\",%u,%u,%u,%u]",i?",":"",e->kind,e->width,e->address,e->value,(unsigned)e->masked); }
        puts("]}");
    }
    return 0;
}
