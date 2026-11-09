#define PCM_SERIAL_TEST_MAIN inherited_serial_main
#include "serial_test.c"
#undef PCM_SERIAL_TEST_MAIN
#include "system.h"

static PcmStatus startup_write8(void *v,uint16_t a,uint8_t value)
{
    Fixture *f=v;
    if (a<0x3000 || a>=0x4000) {
        PcmStatus r=record(f,'W',8,a,value);if (r!=PCM_OK) return r;
    }
    return serial_write8(v,a,value);
}
static PcmStatus startup_write16(void *v,uint16_t a,uint16_t value)
{
    Fixture *f=v;
    if (a<0x3000 || a>=0x4000) {
        PcmStatus r=record(f,'W',16,a,value);if (r!=PCM_OK) return r;
    }
    return serial_write16(v,a,value);
}
static uint32_t startup_digest(const uint8_t *bytes,bool boot)
{
    uint32_t a=1,b=0;
    for (unsigned i=0;i<65536;++i) {
        /* The stock JSR frame uses03FE/03FF; native C has no target frame. */
        uint8_t value=boot && (i==0x3fe || i==0x3ff)?0:bytes[i];
        a=(a+value)%65521u;b=(b+a)%65521u;
    }
    return (b<<16)|a;
}
static void startup_memory_contracts(void)
{
    static Fixture f;Pcm pcm;PcmCalibration root;PcmFuelCalibration fuel;PcmIacCalibration iac;
    PcmAirCalibration air;PcmIoCalibration io;PcmMixtureCalibration mix;PcmFeedbackCalibration fb;PcmDeliveryCalibration dl;
#define INIT() do { serial_init(&f,&pcm,&root,&fuel,&iac,&air,&io,&mix,&fb,&dl); \
    f.platform.write8=startup_write8;f.platform.write16=startup_write16; } while (0)
    INIT();CHECK(pcm_ram_clear(&pcm,0x200,0)==PCM_OK && f.used==1024);
    CHECK(f.events[0].width==16 && f.events[1023].address==0x9fe);
    INIT();CHECK(pcm_ram_clear(&pcm,0x201,9)==PCM_OK && f.used==5);
    CHECK(f.events[0].width==8 && f.events[0].address==0x201 && f.events[1].address==0x202);
    INIT();f.fail_at=3;f.memory[0x204]=0xa5;serial_transfer(&pcm,&f,true);
    CHECK(pcm_ram_clear(&pcm,0x200,8)==PCM_NO_HARDWARE && f.used==2 && f.memory[0x204]==0xa5);
    INIT();pcm.serial.count=0xa5;pcm.serial.receive[0]=0x5a;f.memory[0x3ff]=0x77;
    pcm.runtime.engine_service=true;pcm.serial.sessions=3;pcm.io.raw_coolant=0x99;
    CHECK(pcm_reset_ram(&pcm)==PCM_OK && pcm.serial.count==0 && pcm.serial.receive[0]==0);
    CHECK(!pcm.runtime.engine_service && pcm.serial.sessions==0 && pcm.io.raw_coolant==0 && f.memory[0x3ff]==0x77);
    CHECK(f.memory[0x35]==0 && f.memory[0x100]==0 && f.memory[0x29c]==0 && f.memory[0x8ff]==0);
    INIT();f.platform.write8=NULL;CHECK(pcm_ram_clear(&pcm,0x200,1)==PCM_NO_HARDWARE);
    INIT();f.platform.write16=NULL;CHECK(pcm_ram_clear(&pcm,0x200,8)==PCM_NO_HARDWARE);
#undef INIT
    puts("RAM clear widths/count wrap, failed prefixes, canonical state and startup serial retention pass.");
}
int main(int argc,char **argv)
{
    if (argc==2 && strcmp(argv[1],"--contracts")==0) { startup_memory_contracts();return 0; }
    CHECK(argc==1);
    const char *path=getenv("PCM_SERIAL_ROM");CHECK(path!=NULL);
    FILE *file=fopen(path,"rb");CHECK(file!=NULL && fread(serial_rom,1,65536,file)==65536);
    CHECK(fclose(file)==0);serial_rom_loaded=true;
    static Fixture f;Pcm pcm;PcmCalibration root;PcmFuelCalibration fuel;PcmIacCalibration iac;
    PcmAirCalibration air;PcmIoCalibration io;PcmMixtureCalibration mix;PcmFeedbackCalibration fb;PcmDeliveryCalibration dl;
    unsigned mode,address,count,seed,fail;
    while (scanf("%u %u %u %u %u",&mode,&address,&count,&seed,&fail)==5) {
        CHECK(mode<2 && address<65536 && count<65536 && seed<256 && fail<65536);
        serial_init(&f,&pcm,&root,&fuel,&iac,&air,&io,&mix,&fb,&dl);
        for (unsigned a=0;a<0x4000;++a) f.memory[a]=(uint8_t)(37u*a+seed);
        serial_transfer(&pcm,&f,true);f.platform.write8=startup_write8;f.platform.write16=startup_write16;
        f.masked=true;f.fail_at=fail;
        PcmStatus result=mode?pcm_reset_ram(&pcm):pcm_ram_clear(&pcm,(uint16_t)address,(uint16_t)count);
        serial_transfer(&pcm,&f,false);
        printf("{\"status\":%u,\"digest\":%u,\"events\":[",(unsigned)result,(unsigned)startup_digest(f.memory,mode!=0));
        for (unsigned i=0;i<f.used;++i) { Event *e=&f.events[i];printf("%s[\"%c\",%u,%u,%u,%u]",i?",":"",e->kind,e->width,e->address,e->value,(unsigned)e->masked); }
        puts("]}");
    }
    return 0;
}
