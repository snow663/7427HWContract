#include "board_io.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define CHECK(x) do{if(!(x)){fprintf(stderr,"ADAA TCC:%d: %s\n",__LINE__,#x);exit(3);}}while(0)
typedef struct {PcmPlatform io;uint8_t mem[65536];unsigned ops;} Fixture;
static PcmStatus r8(void *ctx,uint16_t a,uint8_t *v)
{Fixture*f=ctx;++f->ops;*v=f->mem[a];return PCM_OK;}
static PcmStatus r16(void *ctx,uint16_t a,uint16_t *v)
{Fixture*f=ctx;++f->ops;*v=(uint16_t)((uint16_t)f->mem[a]<<8|f->mem[(uint16_t)(a+1u)]);return PCM_OK;}
static PcmStatus w8(void *ctx,uint16_t a,uint8_t v)
{Fixture*f=ctx;++f->ops;f->mem[a]=v;return PCM_OK;}
static const uint16_t OUT[]={0x0089,0x0853,0x0854};
int main(int argc,char**argv)
{
    if(argc!=2)return 2;
    FILE*in=fopen(argv[1],"rb");if(!in)return 2;
    static uint8_t source[65536];static Fixture f;Pcm pcm;
    int n=fread(source,1,sizeof(source),in)==sizeof(source);
    fclose(in);if(!n)return 2;
    unsigned count;
    while(scanf("%u",&count)==1) {
        CHECK(count<1024);
        memset(&f,0,sizeof(f));memset(&pcm,0,sizeof(pcm));
        memcpy(f.mem,source,sizeof(source));
        f.io.context=&f;f.io.read8=r8;f.io.read16=r16;
        f.io.write8=w8;pcm.platform=&f.io;
        for(unsigned i=0;i<count;++i) {
            unsigned a,v;CHECK(scanf("%u %u",&a,&v)==2);
            CHECK(a<65536 && v<256);f.mem[a]=(uint8_t)v;
        }
        PcmStatus status=pcm_tcc_non_electronic(&pcm);
        printf("{\"status\":%u,\"state\":[",(unsigned)status);
        for(unsigned i=0;i<sizeof(OUT)/sizeof(OUT[0]);++i)
            printf("%s%u",i?",":"",(unsigned)f.mem[OUT[i]]);
        puts("]}");
    }
    return 0;
}
