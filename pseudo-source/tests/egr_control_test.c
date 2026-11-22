#define PCM_CONTROLLER_FIXTURE_ENTRY inherited_egr_controller_main
#include "boot_controllers_test.c"
#undef PCM_CONTROLLER_FIXTURE_ENTRY

static void egr_transfer(Pcm *pcm,uint8_t *memory,bool load)
{
    controller_transfer(pcm,memory,load);
    static const Mapping extra[]={
        {0x3b,0,0x10,1,offsetof(Pcm,runtime.engine_service)},
        {0x70,0,4,1,offsetof(Pcm,fuel.alternate_interval)},
        {0x4f,0,0x80,1,offsetof(Pcm,runtime.spark_running)},
    };
    transfer(pcm,memory,extra,SIZE(extra),load);
}
static PcmStatus egr_read8(void *v,uint16_t address,uint8_t *out)
{
    BootFixture *f=v;PcmStatus status=controller_read8(v,address,out);
    if (status!=PCM_OK) return status;
    if (f->action==23 && address==0x6d) f->memory[address]^=8;
    if (f->action==25 && address==0x1ba) f->memory[address]=(uint8_t)(*out+17u);
    if (f->action==26 && address==0x51) f->memory[address]^=0x10;
    if (f->action==27 && address==0x48af) f->memory[address]=(uint8_t)(*out+37u);
    return PCM_OK;
}
static PcmStatus egr_read16(void *v,uint16_t address,uint16_t *out)
{
    BootFixture *f=v;PcmStatus status=boot_read16(v,address,out);
    if (status==PCM_OK && f->action==24 && address==0x1bc) {
        f->memory[address]^=0x55;f->memory[address+1]^=0x55;
    }
    return status;
}
static PcmStatus egr_execute(unsigned mode,Pcm *pcm)
{
    PcmStatus status;
    switch (mode) {
    case 0:return pcm_egr_control(pcm);
    case 1:return pcm_egr_output(pcm);
    case 2:
        status=pcm_egr_control(pcm);return status==PCM_OK?pcm_egr_output(pcm):status;
    case 3:
        status=pcm_egr_feedback(pcm);if (status!=PCM_OK) return status;
        status=pcm_egr_control(pcm);return status==PCM_OK?pcm_egr_output(pcm):status;
    default:return PCM_BAD_CONFIGURATION;
    }
}
int main(int argc,char **argv)
{
    const char *path=getenv("PCM_BOOT_ROM");CHECK(path!=NULL || argc==2);
    if (path!=NULL) { FILE *file=fopen(path,"rb");CHECK(file!=NULL && fread(boot_rom,1,65536,file)==65536);CHECK(fclose(file)==0); }
    CHECK(argc==1 || (argc==2 && strcmp(argv[1],"--contracts")==0));
    static BootFixture f;Pcm pcm;unsigned mode,fail,action,masked,count;bool contracts=argc==2;
    while (contracts || scanf("%u %u %u %u %u",&mode,&fail,&action,&masked,&count)==5) {
        boot_init(&f,&pcm);f.extra_transfer=egr_transfer;f.platform.read8=egr_read8;f.platform.read16=egr_read16;
        f.platform.write8=controller_write8;f.platform.mask_irq=controller_mask;
        if (contracts) {
            f.memory[0x400d]=0;f.memory[0x1ae]=41;f.memory[0x1bc]=0xab;f.memory[0x1bd]=0xcd;
            CHECK(pcm_egr_control(&pcm)==PCM_OK && f.memory[0x1af]==41 && word(f.memory,0x1bc)==0xabcd);
            boot_init(&f,&pcm);f.extra_transfer=egr_transfer;
            f.memory[0x400d]=2;f.memory[0x1ae]=255;f.memory[0x1bc]=0;f.memory[0x1bd]=1;
            f.memory[0x48b5]=0;f.memory[0x48b6]=f.memory[0x48b7]=255;
            CHECK(pcm_egr_control(&pcm)==PCM_OK && word(f.memory,0x1be)==0xff00);
            boot_init(&f,&pcm);f.memory[0x71]=0x80;
            CHECK(pcm_egr_output(&pcm)==PCM_OK && word(f.memory,0x3fd8)==0xf0ff);
            puts("EGR direct-duty retention, FF00 proportional cap and stopped-engine output contracts pass.");return 0;
        }
        CHECK(mode<4 && count<4096);
        for (unsigned i=0;i<count;++i) { unsigned a,value;CHECK(scanf("%u %u",&a,&value)==2 && a<65536 && value<256);f.memory[a]=(uint8_t)value; }
        boot_transfer(&f,true);f.fail=fail;f.action=action;f.masked=masked!=0;
        PcmStatus status=egr_execute(mode,&pcm);boot_transfer(&f,false);
        printf("{\"status\":%u,\"value\":0,\"state\":\"",(unsigned)status);
        for (unsigned a=0;a<0x900;++a) printf("%02x",a>=0x3b0 && a<0x400?0:f.memory[a]);
        hex(f.memory,0x3000,0x3070);hex(f.memory,0x3fc0,0x3ffe);printf("\",\"events\":[");
        for (unsigned i=0;i<f.used;++i) { BootEvent *e=&f.events[i];printf("%s[\"%c\",%u,%u,%u,%u]",i?",":"",e->kind,e->width,e->address,e->value,(unsigned)e->masked); }
        puts("]}");
    }
    return 0;
}
