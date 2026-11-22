/* BMHM D8CE direct pointer-table C fixture and fast failure tests. */
#include "control.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define CHECK(x) do{if(!(x)){fprintf(stderr,"D8CE:%d %s\n",__LINE__,#x);exit(3);}}while(0)
typedef struct {PcmPlatform platform;uint8_t mem[65536];unsigned reads,fail_at;} Fixture;
static PcmStatus r8(void*ctx,uint16_t a,uint8_t*value)
{Fixture*f=ctx;if(++f->reads==f->fail_at)return PCM_NO_HARDWARE;*value=f->mem[a];return PCM_OK;}
static PcmStatus r16(void*ctx,uint16_t a,uint16_t*value)
{Fixture*f=ctx;if(++f->reads==f->fail_at)return PCM_NO_HARDWARE;
 *value=(uint16_t)((uint16_t)f->mem[a]<<8|f->mem[(uint16_t)(a+1u)]);return PCM_OK;}
static void init(Fixture*f,Pcm*p)
{memset(f,0,sizeof(*f));memset(p,0,sizeof(*p));
 f->platform.context=f;f->platform.read8=r8;f->platform.read16=r16;p->platform=&f->platform;}
static unsigned displacement(unsigned range,unsigned slot)
{return (2u*(slot+3u*((range&7u)>>1)))&255u;}
static void contracts(void)
{
    static Fixture f;Pcm p;uint8_t value;bool valid;
    init(&f,&p);f.mem[0x98]=4;value=99;valid=true;
    CHECK(pcm_transmission_threshold_select(&p,0xd763,2,&value,&valid)==PCM_OK);
    CHECK(value==0&&!valid&&f.reads==1);
    init(&f,&p);value=99;valid=true;
    CHECK(pcm_transmission_threshold_select(&p,0xd763,2,&value,&valid)==PCM_OK);
    CHECK(value==0&&!valid&&f.reads==2);
    for(unsigned range=1;range<256;range++)for(unsigned slot=0;slot<256;slot++) {
        init(&f,&p);f.mem[0xa2]=(uint8_t)range;
        unsigned addr=0xd763+displacement(range,slot);
        f.mem[addr]=0x12;f.mem[addr+1]=0x34;f.mem[0x1234]=(uint8_t)(range^slot);
        value=0;valid=false;
        CHECK(pcm_transmission_threshold_select(&p,0xd763,(uint8_t)slot,&value,&valid)==PCM_OK);
        CHECK(value==(uint8_t)(range^slot)&&valid&&f.reads==4);
    }
    for(unsigned fail=1;fail<=4;fail++) {
        init(&f,&p);f.mem[0xa2]=2;f.mem[0xd76b]=0x12;f.mem[0xd76c]=0x34;
        f.fail_at=fail;value=17;valid=true;
        CHECK(pcm_transmission_threshold_select(&p,0xd763,1,&value,&valid)==PCM_NO_HARDWARE);
        CHECK(f.reads==fail&&value==17&&valid);
    }
    CHECK(pcm_transmission_threshold_select(NULL,0xd763,1,&value,&valid)==PCM_BAD_CONFIGURATION);
    CHECK(pcm_transmission_threshold_select(&p,0xd763,1,NULL,&valid)==PCM_BAD_CONFIGURATION);
    CHECK(pcm_transmission_threshold_select(&p,0xd763,1,&value,NULL)==PCM_BAD_CONFIGURATION);
    puts("D8CE: all range/candidate pointer offsets, carry-invalid and four failed-read prefixes pass.");
}
int main(int argc,char**argv)
{
    if(argc==2&&strcmp(argv[1],"--contracts")==0){contracts();return 0;}
    if(argc!=2)return 2;
    static Fixture f;Pcm p;static uint8_t image[65536];
    FILE*in=fopen(argv[1],"rb");if(!in)return 2;
    int good=fread(image,1,sizeof(image),in)==sizeof(image);fclose(in);
    if(!good)return 2;
    unsigned table,slot,count;
    while(scanf("%u %u %u",&table,&slot,&count)==3) {
        CHECK(table<65536 && slot<256 && count<1024);
        init(&f,&p);memcpy(f.mem,image,sizeof(image));
        for(unsigned i=0;i<count;i++){
            unsigned address,v;CHECK(scanf("%u %u",&address,&v)==2);
            CHECK(address<65536&&v<256);f.mem[address]=(uint8_t)v;
        }
        uint8_t value=0;bool valid=false;
        PcmStatus status=pcm_transmission_threshold_select(&p,(uint16_t)table,(uint8_t)slot,&value,&valid);
        printf("{\"status\":%u,\"value\":%u,\"valid\":%u}\n",
            (unsigned)status,(unsigned)value,(unsigned)valid);
    }
    return ferror(stdin)?2:0;
}
