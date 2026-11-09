#define main inherited_reference_main
#include "reference_event_test.c"
#undef main
#include "system.h"
#include "startup.h"
#include "service_fixture_map.h"

#define SIZE(a) (sizeof(a)/sizeof(*(a)))
#define CHECK(c) do { if (!(c)) { fprintf(stderr,"Boot fixture check %d: %s\n",__LINE__,#c);exit(1); } } while (0)
typedef struct { char kind;unsigned width;uint16_t address,value;bool masked; } BootEvent;
typedef struct {
    uint8_t memory[65536];BootEvent events[65536];unsigned used,attempts,fail,action;
    bool masked;Pcm *pcm;PcmPlatform platform;
} BootFixture;
static uint8_t boot_rom[65536];
#define B(a,m) {a,8,0,1,offsetof(Pcm,m)}
#define W(a,m) {a,16,0,1,offsetof(Pcm,m)}
#define F(a,b,m) {a,0,b,1,offsetof(Pcm,m)}
#define A(a,n,m) {a,8,0,n,offsetof(Pcm,m)}
static const Mapping boot_state_map[]={
 B(1,system.factory_flags),F(0x1a,0x20,runtime.special_fast_group),F(0x3a,1,runtime.adc_fault),
 F(0x3a,0x20,scheduler.pending),F(0x46,0x40,fuel.blm_invalid),
 B(0x2f6,iac.tps_zero_high),B(0x2f7,iac.tps_zero_low),A(0x2b3,21,fuel.blm_cells),
 W(0x1f6,system.initial_spark),B(7,iac.position),B(8,iac.target),B(9,iac.state_flags),B(10,iac.step_control),
 B(0x82f,io.diagnostic_sample),F(0x86,0x40,scheduler.profiling_enabled),F(0x19,4,fuel.oxygen_fault_a),
};
#undef B
#undef W
#undef F
#undef A
static void boot_transfer(BootFixture *f,bool load)
{
    transfer(f->pcm,f->memory,state_map,SIZE(state_map),load);
    transfer(f->pcm,f->memory,service_state_map,SIZE(service_state_map),load);
    transfer(f->pcm,f->memory,boot_state_map,SIZE(boot_state_map),load);
}
static PcmStatus boot_record(BootFixture *f,char kind,unsigned width,uint16_t address,uint16_t value)
{
    if (++f->attempts==f->fail) return PCM_NO_HARDWARE;
    CHECK(f->used<SIZE(f->events));
    f->events[f->used++]=(BootEvent){kind,width,address,value,f->masked};return PCM_OK;
}
static PcmStatus boot_read8(void *v,uint16_t a,uint8_t *out)
{
    BootFixture *f=v;boot_transfer(f,false);uint8_t value=f->memory[a];
    PcmStatus r=boot_record(f,'R',8,a,value);if (r!=PCM_OK) return r;*out=value;
    if (f->action==1 && a==0x5bca) ++f->memory[a];
    if (f->action==2 && a==0x82f) { f->memory[a]=0;f->pcm->io.diagnostic_sample=0; }
    if (f->action==3 && a==0x15) f->pcm->system.diagnostic_checksum^=0xff;
    return PCM_OK;
}
static PcmStatus boot_read16(void *v,uint16_t a,uint16_t *out)
{
    BootFixture *f=v;boot_transfer(f,false);uint16_t value=word(f->memory,a);
    PcmStatus r=boot_record(f,'R',16,a,value);if (r==PCM_OK) *out=value;return r;
}
static PcmStatus boot_write8(void *v,uint16_t a,uint8_t value)
{
    BootFixture *f=v;boot_transfer(f,false);
    PcmStatus r=boot_record(f,'W',8,a,value);if (r!=PCM_OK) return r;
    f->memory[a]=value;boot_transfer(f,true);return PCM_OK;
}
static PcmStatus boot_write16(void *v,uint16_t a,uint16_t value)
{
    BootFixture *f=v;boot_transfer(f,false);
    PcmStatus r=boot_record(f,'W',16,a,value);if (r!=PCM_OK) return r;
    f->memory[a]=(uint8_t)(value>>8);f->memory[(uint16_t)(a+1u)]=(uint8_t)value;
    boot_transfer(f,true);return PCM_OK;
}
static PcmStatus boot_delay(void *v,uint16_t cycles)
{ return boot_record(v,'D',0,0,cycles); }
static void boot_init(BootFixture *f,Pcm *pcm)
{
    memset(f,0,sizeof(*f));memset(pcm,0,sizeof(*pcm));f->pcm=pcm;
    memcpy(f->memory,boot_rom,sizeof(boot_rom));memset(f->memory,0,0x4000);
    f->platform.context=f;f->platform.read8=boot_read8;f->platform.read16=boot_read16;
    f->platform.write8=boot_write8;f->platform.write16=boot_write16;f->platform.delay_cycles=boot_delay;
    pcm->platform=&f->platform;pcm->unresolved_task=PCM_TASK_COUNT;
}
static PcmStatus boot_execute(unsigned mode,BootFixture *f,uint16_t *out)
{
    switch (mode) {
    case 0:return pcm_rom_checksum(f->pcm,out);
    case 1:return pcm_boot_rom_validate(f->pcm);
    case 2:return pcm_boot_retained_validate(f->pcm);
    case 3:return pcm_boot_adaptive_validate(f->pcm);
    case 4:return pcm_boot_recovery(f->pcm);
    case 5:return pcm_reset_retained(f->pcm);
    default:return PCM_BAD_CONFIGURATION;
    }
}
static void boot_contracts(void)
{
    static BootFixture f;Pcm pcm;uint16_t out=0x5aa5;
    boot_init(&f,&pcm);CHECK(pcm_rom_checksum(&pcm,NULL)==PCM_BAD_CONFIGURATION && f.used==0);
    f.fail=1;CHECK(pcm_rom_checksum(&pcm,&out)==PCM_NO_HARDWARE && out==0x5aa5);
    boot_init(&f,&pcm);f.memory[0x303f]=0;pcm.io.diagnostic_sample=100;f.action=2;
    CHECK(pcm_boot_rom_validate(&pcm)==PCM_BOOT_WAIT_BOUNDARY && pcm.io.diagnostic_sample==0);
    CHECK(pcm.system.configuration_failure && pcm.system.boot_output_inhibit && pcm.runtime.special_fast_group);
    boot_init(&f,&pcm);CHECK(pcm_boot_adaptive_validate(&pcm)==PCM_OK && pcm.system.adaptive_failure);
    for (unsigned a=0x2f8;a<=0x32b;++a) CHECK(f.memory[a]==128);
    f.used=f.attempts=0;CHECK(pcm_boot_adaptive_validate(&pcm)==PCM_OK && f.used==52);
    boot_init(&f,&pcm);pcm.system.diagnostic_checksum=1;
    CHECK(pcm_boot_retained_validate(&pcm)==PCM_OK && pcm.fuel.blm_invalid && pcm.system.retained_initialized);
    for (unsigned i=0;i<21;++i) CHECK(pcm.fuel.blm_cells[i]==128);
    CHECK(pcm.iac.tps_zero_low==128);
    puts("Boot wait capture, checksum failed-output retention, adaptive revalidation and canonical recovery joins pass.");
}
int main(int argc,char **argv)
{
    bool contracts=argc==2 && strcmp(argv[1],"--contracts")==0;
    const char *path=getenv("PCM_BOOT_ROM");CHECK(path!=NULL || contracts);
    if (path!=NULL) {
        FILE *file=fopen(path,"rb");CHECK(file!=NULL && fread(boot_rom,1,65536,file)==65536);CHECK(fclose(file)==0);
    }
    if (argc==2 && strcmp(argv[1],"--contracts")==0) { boot_contracts();return 0; }
    CHECK(argc==1);static BootFixture f;Pcm pcm;unsigned mode,count,fail,action,masked;
    while (scanf("%u %u %u %u %u",&mode,&fail,&action,&masked,&count)==5) {
        CHECK(mode<6 && count<4096);boot_init(&f,&pcm);
        for (unsigned i=0;i<count;++i) { unsigned a,v;CHECK(scanf("%u %u",&a,&v)==2 && a<65536 && v<256);f.memory[a]=(uint8_t)v; }
        boot_transfer(&f,true);f.fail=fail;f.action=action;f.masked=masked!=0;uint16_t out=0x5aa5;
        PcmStatus r=boot_execute(mode,&f,&out);boot_transfer(&f,false);
        printf("{\"status\":%u,\"value\":%u,\"state\":\"",(unsigned)r,(unsigned)out);
        for (unsigned a=0;a<0x900;++a) printf("%02x",a>=0x3b0 && a<0x400?0:f.memory[a]);
        hex(f.memory,0x3000,0x3070);hex(f.memory,0x3fc0,0x3ffe);
        printf("\",\"events\":[");
        for (unsigned i=0;i<f.used;++i) { BootEvent *e=&f.events[i];printf("%s[\"%c\",%u,%u,%u,%u]",i?",":"",e->kind,e->width,e->address,e->value,(unsigned)e->masked); }
        puts("]}");
    }
    return 0;
}
