/* D5B7..D69E source C state fixture, with injected bus failures. */
#include "control.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define CHECK(x) do{if(!(x)){fprintf(stderr,"D5B7:%d %s\n",__LINE__,#x);exit(3);}}while(0)
typedef struct {PcmPlatform platform;uint8_t mem[65536];uint16_t addresses[256];unsigned ops,fail_at;} Fixture;
static PcmStatus read8(void*ctx,uint16_t addr,uint8_t*value)
{
    Fixture*f=ctx;
    unsigned op=f->ops++;if(op<256)f->addresses[op]=addr;
    if(f->ops==f->fail_at)return PCM_NO_HARDWARE;
    *value=f->mem[addr];return PCM_OK;
}
static PcmStatus write8(void*ctx,uint16_t addr,uint8_t value)
{
    Fixture*f=ctx;
    unsigned op=f->ops++;if(op<256)f->addresses[op]=addr;
    if(f->ops==f->fail_at)return PCM_NO_HARDWARE;
    f->mem[addr]=value;return PCM_OK;
}
static void init(Fixture*f,Pcm*p)
{
    memset(f,0,sizeof(*f));memset(p,0,sizeof(*p));
    f->platform.context=f;f->platform.read8=read8;f->platform.write8=write8;
    p->platform=&f->platform;
}
static const uint16_t OUT[]={0x0083,0x0085,0x00d9,0x0135,0x0187,0x0103};
static void contracts(void)
{
    static Fixture f;Pcm p;
    init(&f,&p);
    f.mem[0x00a2]=0;f.mem[0x00d9]=1;
    f.mem[0xe57c+12+3]=3;
    CHECK(pcm_transmission_gear_finalize(&p,3)==PCM_OK);
    CHECK(f.mem[0x00d9]==3 && (f.mem[0x0083]&5u)==5u);
    init(&f,&p);
    f.mem[0x0103]=5;f.mem[0x0187]=0;
    CHECK(pcm_transmission_gear_finalize(&p,1)==PCM_OK);
    CHECK(f.mem[0x0103]==4 && f.mem[0x0187]==255 &&
          f.mem[0x00d9]==3);
    init(&f,&p);f.mem[0x83]=0xff;f.fail_at=1;
    CHECK(pcm_transmission_gear_finalize(&p,1)==PCM_NO_HARDWARE);
    CHECK(f.mem[0x83]==0xff && f.ops==1);
    init(&f,&p);f.mem[0x0099]=1;f.mem[0x00d9]=2;
    f.mem[0x0083]=0xa5;f.fail_at=4;
    CHECK(pcm_transmission_gear_finalize(&p,2)==PCM_NO_HARDWARE);
    CHECK(f.ops==4 && f.addresses[0]==0x0099 &&
          f.addresses[1]==0x0099 && f.addresses[2]==0x00d9 &&
          f.addresses[3]==0x00d9);
    CHECK(f.mem[0x0083]==0xa5 && f.mem[0x00d9]==2);
    CHECK(pcm_transmission_gear_finalize(NULL,1)==PCM_BAD_CONFIGURATION);
    puts("D5B7 gear arbitration: direct upshift, override and fail-at-first-prefix pass.");
}
int main(int argc,char **argv)
{
    if(argc==2 && strcmp(argv[1],"--contracts")==0){contracts();return 0;}
    if(argc!=2)return 2;
    static uint8_t rom[65536];static Fixture f;Pcm pcm;
    FILE*in=fopen(argv[1],"rb");if(!in)return 2;
    int good=fread(rom,1,sizeof(rom),in)==sizeof(rom);
    fclose(in);if(!good)return 2;
    unsigned candidate,count;
    while(scanf("%u %u",&candidate,&count)==2){
        CHECK(candidate<256&&count<1024);
        init(&f,&pcm);memcpy(f.mem,rom,sizeof(rom));
        for(unsigned i=0;i<count;++i){
            unsigned addr,value;CHECK(scanf("%u %u",&addr,&value)==2);
            CHECK(addr<65536 && value<256);f.mem[addr]=(uint8_t)value;
        }
        PcmStatus status=pcm_transmission_gear_finalize(&pcm,(uint8_t)candidate);
        printf("{\"status\":%u,\"state\":[",(unsigned)status);
        for(unsigned i=0;i<sizeof(OUT)/sizeof(OUT[0]);++i)
            printf("%s%u",i?",":"",(unsigned)f.mem[OUT[i]]);
        puts("]}");
    }
    return ferror(stdin)?2:0;
}
