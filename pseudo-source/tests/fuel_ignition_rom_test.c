/* Machine-readable $7D4B..$7DB5 ignition/initialization comparisons.
 * Only the test fixture holds a 65536-byte memory image. */
#include "fuel.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define CHECK(x) do { if(!(x)) { fprintf(stderr,"Ignition ROM fixture %s:%d: %s\n",__FILE__,__LINE__,#x);return 3;} }while(0)
typedef struct {
    uint8_t bytes[65536];
    PcmPlatform io;
    bool masked;
} Fixture;
static PcmStatus read8(void *v,uint16_t a,uint8_t *out)
{
    Fixture *f=v;*out=f->bytes[a];return PCM_OK;
}
static PcmStatus read16(void *v,uint16_t a,uint16_t *out)
{
    Fixture *f=v;*out=(uint16_t)((uint16_t)f->bytes[a]<<8|f->bytes[(uint16_t)(a+1u)]);
    return PCM_OK;
}
static PcmStatus write8(void *v,uint16_t a,uint8_t val)
{
    Fixture *f=v;f->bytes[a]=val;return PCM_OK;
}
static PcmStatus write16(void *v,uint16_t a,uint16_t val)
{
    Fixture *f=v;f->bytes[a]=(uint8_t)(val>>8);
    f->bytes[(uint16_t)(a+1u)]=(uint8_t)val;return PCM_OK;
}
static PcmStatus mask(void *v,bool on)
{
    Fixture *f=v;f->masked=on;return PCM_OK;
}
static const uint16_t ADDRESSES[]={
    0x0004,0x0019,0x003e,0x0044,0x0046,0x004f,0x0051,0x0062,0x0086,
    0x00fd,0x00fe,0x0223,0x024c,0x024d,0x0268,0x027d,0x027e,0x027f,
    0x02cd,0x02ce,0x3039,0x303a
};
int main(int argc,char **argv)
{
    if(argc!=2)return 2;
    FILE *p=fopen(argv[1],"rb");if(!p)return 2;
    static uint8_t factory[65536];
    int ok=fread(factory,1,sizeof(factory),p)==sizeof(factory);
    fclose(p);if(!ok)return 2;
    static Fixture fixture;Pcm pcm;
    unsigned pairs;
    while(scanf("%u",&pairs)==1) {
        CHECK(pairs<1024);
        memset(&pcm,0,sizeof(pcm));
        memcpy(fixture.bytes,factory,sizeof(factory));
        fixture.masked=false;
        for(unsigned k=0;k<pairs;++k) {
            unsigned addr,v;CHECK(scanf("%u %u",&addr,&v)==2);
            CHECK(addr<65536 && v<256);
            fixture.bytes[addr]=(uint8_t)v;
        }
        memset(&fixture.io,0,sizeof(fixture.io));
        fixture.io.context=&fixture;fixture.io.read8=read8;fixture.io.read16=read16;
        fixture.io.write8=write8;fixture.io.write16=write16;fixture.io.mask_irq=mask;
        pcm.platform=&fixture.io;
        PcmStatus status=pcm_fuel_ignition_precheck(&pcm);
        printf("{\"status\":%u,\"masked\":%u,\"state\":[",
               (unsigned)status,(unsigned)fixture.masked);
        for(unsigned i=0;i<sizeof(ADDRESSES)/sizeof(ADDRESSES[0]);++i)
            printf("%s%u",i?",":"",(unsigned)fixture.bytes[ADDRESSES[i]]);
        puts("]}");
    }
    return ferror(stdin)?2:0;
}
