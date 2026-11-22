#define PCM_EGR_FIXTURE_ENTRY inherited_egr_fixture_main
#include "egr_control_test.c"
#undef PCM_EGR_FIXTURE_ENTRY
#include "spark.h"
#include "fuel.h"

static void producer_transfer(Pcm *pcm,uint8_t *memory,bool load)
{
    egr_transfer(pcm,memory,load);
    static const Mapping extra[]={
        {0x6e,0,0x80,1,offsetof(Pcm,spark.egr_active)},
        {0x1b2,8,0,1,offsetof(Pcm,spark.egr_fraction_high)},
        {0x1b3,8,0,1,offsetof(Pcm,fuel.egr_fraction_low)},
        {0x1f4,16,0,1,offsetof(Pcm,spark.egr_filtered)},
        {0x232,8,0,1,offsetof(Pcm,iac.runtime_high)},
        {0x233,8,0,1,offsetof(Pcm,fuel.air_rate_fraction)},
        {0x24e,16,0,1,offsetof(Pcm,fuel.corrected_pulse)},
        {0x252,16,0,1,offsetof(Pcm,fuel.egr_subtract)},
        {0x248,8,0,1,offsetof(Pcm,iac.blm_value)},
        {0x284,8,0,1,offsetof(Pcm,spark.vehicle_speed_high)},
        {0x1cf,8,0,1,offsetof(Pcm,spark.normalized_load)},
    };
    transfer(pcm,memory,extra,SIZE(extra),load);
}
static PcmStatus producer_read8(void *v,uint16_t address,uint8_t *out)
{
    BootFixture *f=v;PcmStatus status=egr_read8(v,address,out);if (status!=PCM_OK) return status;
    if (f->action==28 && address==0x470a) f->memory[address]^=2;
    if (f->action==29 && (address==0x470d || address==0x4769 || address==0x478c || address==0x47e7))
        f->memory[address]=(uint8_t)(*out+17u);
    if (f->action==31 && address==0x6e) f->memory[address]^=0xf4;
    if (f->action==32 && address==0x400d) f->memory[address]^=0x26;
    if (f->action==33 && address==0x1c0) f->memory[address]=(uint8_t)(*out+17u);
    if (f->action==34 && address==0x232) f->memory[address]=(uint8_t)(*out+17u);
    boot_transfer(f,true);return PCM_OK;
}
static PcmStatus producer_read16(void *v,uint16_t address,uint16_t *out)
{
    BootFixture *f=v;PcmStatus status=egr_read16(v,address,out);if (status!=PCM_OK) return status;
    if (f->action==30 && address>=0x470e && address<0x48a4) f->memory[address]=(uint8_t)(f->memory[address]+11u);
    if (f->action==34 && address==0x232) f->memory[address]^=0x55;
    boot_transfer(f,true);return PCM_OK;
}
static PcmStatus producer_call(void *v,uint16_t address)
{
    BootFixture *f=v;CHECK(address==0x1815);
    PcmStatus status=boot_record(f,'C',0,address,0);if (status!=PCM_OK) return status;
    if (f->action==36) return PCM_UNIMPLEMENTED;
    if (f->action==35) { f->memory[0x1ae]=123;f->memory[0x3b]|=0x10;f->memory[0x393]=2; }
    boot_transfer(f,true);return PCM_OK;
}
static void producer_init(BootFixture *f,Pcm *pcm)
{
    boot_init(f,pcm);f->extra_transfer=producer_transfer;
    f->platform.read8=producer_read8;f->platform.read16=producer_read16;
    f->platform.write8=controller_write8;f->platform.mask_irq=controller_mask;
    f->platform.call_address=producer_call;
}
static PcmStatus producer_execute(unsigned mode,BootFixture *f)
{
    Pcm *pcm=f->pcm;PcmStatus status;
    switch (mode) {
    case 0:return pcm_egr_demand(pcm);
    case 1:return pcm_egr_flow(pcm);
    case 2:
        status=pcm_egr_demand(pcm);if (status!=PCM_OK) return status;
        status=pcm_egr_feedback(pcm);if (status!=PCM_OK) return status;
        status=pcm_egr_control(pcm);if (status!=PCM_OK) return status;
        status=pcm_egr_flow(pcm);return status==PCM_OK?pcm_egr_output(pcm):status;
    case 3:
        status=pcm_egr_flow(pcm);return status==PCM_OK?pcm_fuel_egr_blm(pcm):status;
    case 4: {
        status=pcm_egr_flow(pcm);if (status!=PCM_OK) return status;
        PcmCalibration root=pcm_reference_scheduler_calibration;PcmSparkCalibration spark=pcm_reference_spark_calibration;
        spark.egr_bias=f->memory[0x413e];spark.egr_mode=f->memory[0x485f];spark.egr_gain=f->memory[0x485e];
        spark.egr=(PcmTable2D){f->memory[0x4860],f->memory[0x4861],f->memory[0x4862],527,f->memory+0x4863};
        root.spark=&spark;pcm->calibration=&root;status=pcm_spark_egr(pcm);pcm->calibration=NULL;return status;
    }
    default:return PCM_BAD_CONFIGURATION;
    }
}
static void producer_contracts(void)
{
    static BootFixture f;Pcm pcm;
    producer_init(&f,&pcm);f.memory[0x51]=0x10;f.memory[0x3b]=0x10;f.memory[0x393]=2;f.memory[0x394]=77;
    boot_transfer(&f,true);CHECK(pcm_egr_demand(&pcm)==PCM_OK && f.memory[0x1ae]==77);
    producer_init(&f,&pcm);f.memory[0x400d]=2;f.memory[0x70]=1;
    f.memory[0x1cc]=96;f.memory[0x4856]=f.memory[0x4857]=255;
    f.memory[0x47ce]=f.memory[0x47cf]=255;boot_transfer(&f,true);
    CHECK(pcm_egr_flow(&pcm)==PCM_OK && f.memory[0x1b1]==0 && word(f.memory,0x1b2)==0xfd02);
    CHECK(pcm.spark.egr_fraction_high==0xfd && pcm.fuel.egr_fraction_low==2 && !pcm.spark.egr_active);
    producer_init(&f,&pcm);pcm.scheduler.profiling_enabled=true;f.platform.call_address=NULL;
    CHECK(pcm_egr_demand(&pcm)==PCM_NO_HARDWARE && f.memory[0x1ae]==0);
    puts("EGR service override, zero-divisor fraction, shared fuel/spark owners and optional-hook boundary contracts pass.");
}
int main(int argc,char **argv)
{
    const char *path=getenv("PCM_BOOT_ROM");CHECK(path!=NULL || argc==2);
    if (path!=NULL) { FILE *file=fopen(path,"rb");CHECK(file!=NULL && fread(boot_rom,1,65536,file)==65536);CHECK(fclose(file)==0); }
    CHECK(argc==1 || (argc==2 && strcmp(argv[1],"--contracts")==0));
    if (argc==2) { producer_contracts();return 0; }
    static BootFixture f;Pcm pcm;unsigned mode,fail,action,masked,count;
    while (scanf("%u %u %u %u %u",&mode,&fail,&action,&masked,&count)==5) {
        CHECK(mode<5 && count<4096);producer_init(&f,&pcm);
        for (unsigned i=0;i<count;++i) { unsigned a,value;CHECK(scanf("%u %u",&a,&value)==2 && a<65536 && value<256);f.memory[a]=(uint8_t)value; }
        boot_transfer(&f,true);f.fail=fail;f.action=action;f.masked=masked!=0;
        if (action==37) f.platform.call_address=NULL;
        PcmStatus status=producer_execute(mode,&f);boot_transfer(&f,false);
        printf("{\"status\":%u,\"value\":0,\"state\":\"",(unsigned)status);
        for (unsigned a=0;a<0x900;++a) printf("%02x",a>=0x3b0 && a<0x400?0:f.memory[a]);
        hex(f.memory,0x3000,0x3070);hex(f.memory,0x3fc0,0x3ffe);printf("\",\"events\":[");
        for (unsigned i=0;i<f.used;++i) { BootEvent *e=&f.events[i];printf("%s[\"%c\",%u,%u,%u,%u]",i?",":"",e->kind,e->width,e->address,e->value,(unsigned)e->masked); }
        puts("]}");
    }
    return 0;
}
