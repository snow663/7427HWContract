#include "fuel.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define CHECK(x) do { if(!(x)){fprintf(stderr,"Governor $90D3 %s:%d: %s\n",__FILE__,__LINE__,#x);exit(1);} }while(0)
typedef struct { char kind; uint16_t address,value; } Event;
typedef struct {
    uint8_t ram[65536];
    Event events[20];unsigned used,attempts,fail_at;
    bool mutate_first_knot;
    PcmPlatform platform;
} Fixture;
static PcmStatus note(Fixture *f,char kind,uint16_t address,uint16_t value)
{
    if(++f->attempts==f->fail_at)return PCM_NO_HARDWARE;
    CHECK(f->used<sizeof(f->events)/sizeof(f->events[0]));
    f->events[f->used++]=(Event){kind,address,value};
    return PCM_OK;
}
static PcmStatus read8(void *ctx,uint16_t address,uint8_t *sample)
{
    Fixture *f=ctx;uint8_t value=f->ram[address];
    PcmStatus status=note(f,'r',address,value);
    if(status==PCM_OK)*sample=value;
    return status;
}
static PcmStatus read16(void *ctx,uint16_t address,uint16_t *sample)
{
    Fixture *f=ctx;
    uint16_t value=(uint16_t)((uint16_t)f->ram[address]*256u+f->ram[(uint16_t)(address+1u)]);
    PcmStatus status=note(f,'R',address,value);
    if(status==PCM_OK) {
        *sample=value;
        if(address==0x5100 && f->mutate_first_knot)f->ram[address]=0x90;
    }
    return status;
}
static PcmStatus write16(void *ctx,uint16_t address,uint16_t value)
{
    Fixture *f=ctx;
    PcmStatus status=note(f,'W',address,value);
    if(status==PCM_OK) {
        f->ram[address]=(uint8_t)(value>>8);
        f->ram[(uint16_t)(address+1u)]=(uint8_t)value;
    }
    return status;
}
static void init(Fixture *f,Pcm *pcm,unsigned desired,unsigned actual,
                 uint16_t accumulator,uint8_t p_gain,uint8_t i_gain)
{
    memset(f,0,sizeof(*f));memset(pcm,0,sizeof(*pcm));
    f->platform.context=f;f->platform.read8=read8;f->platform.read16=read16;f->platform.write16=write16;
    pcm->platform=&f->platform;
    pcm->transmission.governor_requested_throttle=(uint8_t)desired;
    pcm->reference.throttle=(uint8_t)actual;
    pcm->transmission.governor_integrator=accumulator;
    /* Scale zero repeats the first knot exactly for all 8-bit errors. */
    f->ram[0x50ff]=0;f->ram[0x5100]=p_gain;f->ram[0x5101]=p_gain;
    f->ram[0x5109]=0;f->ram[0x510a]=i_gain;f->ram[0x510b]=i_gain;
}
static uint16_t oracle(uint8_t desired,uint8_t actual,uint16_t acc,
                       uint8_t prop_gain,uint8_t integral_gain,uint16_t *next)
{
    uint8_t error=(uint8_t)(desired>actual?desired-actual:actual-desired);
    uint32_t p=(uint32_t)prop_gain*error*4u;
    uint16_t prop=(uint16_t)(p>65535u?65535u:p);
    uint16_t integral=(uint16_t)((uint16_t)integral_gain*error);
    unsigned pwm;
    if(desired<actual) {
        uint32_t sum=(uint32_t)acc+integral;
        acc=(uint16_t)(sum>65535u?0xff00u:sum);
        sum=(uint32_t)acc+prop+128u;
        pwm=sum>65535u?255u:sum>>8;
    } else {
        acc=acc>integral?(uint16_t)(acc-integral):0;
        if(acc<prop)pwm=0;
        else {uint32_t sum=(uint32_t)acc-prop+128u;pwm=sum>65535u?255u:sum>>8;}
    }
    *next=desired==255u?0:acc;
    return (uint16_t)(0x1f00u|(uint8_t)pwm);
}
static void test_arithmetic(void)
{
    static Fixture f;
    Pcm pcm;
    const uint8_t gains[][2]={{0,0},{1,2},{17,99},{255,255}};
    const uint16_t accs[]={0,0x7f80,0xff00,0xffff};
    for(unsigned variant=0;variant<4;++variant)
        for(unsigned desired=0;desired<=255;++desired)
            for(unsigned actual=0;actual<=255;++actual) {
                uint16_t next;
                init(&f,&pcm,desired,actual,accs[variant],gains[variant][0],gains[variant][1]);
                uint16_t expected=oracle((uint8_t)desired,(uint8_t)actual,accs[variant],
                    gains[variant][0],gains[variant][1],&next);
                CHECK(pcm_fuel_governor_drive(&pcm)==PCM_OK);
                CHECK((uint16_t)((uint16_t)f.ram[0x306c]*256u+f.ram[0x306d])==expected);
                CHECK(pcm.transmission.governor_integrator==next);
                CHECK(pcm.transmission.governor_throttle_error==(uint8_t)
                    (desired>=actual?desired-actual:actual-desired));
                CHECK(f.used==9);
                CHECK(f.events[0].kind=='r' && f.events[0].address==0x50ff);
                CHECK(f.events[1].kind=='R' && f.events[1].address==0x5100);
                CHECK(f.events[2].kind=='r' && f.events[2].address==0x5100);
                CHECK(f.events[3].kind=='r' && f.events[3].address==0x5109);
                CHECK(f.events[4].kind=='R' && f.events[4].address==0x510a);
                CHECK(f.events[5].kind=='r' && f.events[5].address==0x510a);
                CHECK(f.events[6].address==0x0051 && f.events[7].address==0x003b);
                CHECK(f.events[8].kind=='W' && f.events[8].address==0x306c);
            }
    puts("262144 governor desired/actual/gain/accumulator histories pass.");
}
static void test_override_and_mutation(void)
{
    static Fixture f;Pcm pcm;
    init(&f,&pcm,5,200,0x1234,19,5);f.ram[0x0051]=0x10;
    CHECK(pcm_fuel_governor_drive(&pcm)==PCM_OK);
    CHECK(f.ram[0x306c]==0x1f && f.ram[0x306d]==0 && f.used==8);
    init(&f,&pcm,5,200,0x1234,19,5);
    f.ram[0x003b]=0x10;f.ram[0x0393]=1;f.ram[0x0394]=0x73;
    CHECK(pcm_fuel_governor_drive(&pcm)==PCM_OK);
    CHECK(f.ram[0x306d]==0x73 && f.used==11);
    init(&f,&pcm,5,200,0x1234,19,5);
    f.mutate_first_knot=true;
    CHECK(pcm_fuel_governor_drive(&pcm)==PCM_OK);
    CHECK(f.events[1].value==0x1313 && f.events[2].value==0x90);
    CHECK(pcm.transmission.governor_proportional!=(uint16_t)(19u*195u*4u));
}
static void test_failure_prefixes(void)
{
    static Fixture f;Pcm pcm;
    for(unsigned mode=0;mode<3;++mode) {
        init(&f,&pcm,10,240,0x1234,44,10);
        if(mode==1)f.ram[0x0051]=0x10;
        if(mode==2){f.ram[0x003b]=0x10;f.ram[0x0393]=1;f.ram[0x0394]=0x42;}
        CHECK(pcm_fuel_governor_drive(&pcm)==PCM_OK);
        Event prior[20];unsigned used=f.used;
        memcpy(prior,f.events,used*sizeof(Event));
        for(unsigned stop=1;stop<=used;++stop) {
            init(&f,&pcm,10,240,0x1234,44,10);
            if(mode==1)f.ram[0x0051]=0x10;
            if(mode==2){f.ram[0x003b]=0x10;f.ram[0x0393]=1;f.ram[0x0394]=0x42;}
            f.fail_at=stop;
            CHECK(pcm_fuel_governor_drive(&pcm)==PCM_NO_HARDWARE);
            CHECK(f.attempts==stop && f.used==stop-1u);
            for(unsigned i=0;i<f.used;++i) {
                CHECK(prior[i].kind==f.events[i].kind);
                CHECK(prior[i].address==f.events[i].address);
                CHECK(prior[i].value==f.events[i].value);
            }
        }
    }
    CHECK(pcm_fuel_governor_drive(NULL)==PCM_BAD_CONFIGURATION);
    puts("Ordered source transactions, mutation and all failure prefixes pass.");
}
int main(int argc,char **argv)
{
    if(argc==2 && strcmp(argv[1],"--contracts")!=0)return 2;
    test_arithmetic();test_override_and_mutation();test_failure_prefixes();
    return 0;
}
