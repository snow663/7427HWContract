/* E562 ROM/C test fixture. Read-only host bus with injected failures.
 * The backing ROM is validated separately by the Python reference replay. */
#include "control.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define CHECK(x) do {if(!(x)){fprintf(stderr,"E562:%d %s\n",__LINE__,#x);exit(3);}}while(0)
typedef struct {
    PcmPlatform platform;
    uint8_t rom[65536];
    uint16_t addresses[4];
    unsigned reads,fail_at;
} Fixture;
static PcmStatus read8(void *opaque,uint16_t addr,uint8_t *value)
{
    Fixture *f=opaque;
    CHECK(f->reads<4);
    f->addresses[f->reads++]=addr;
    if(f->reads==f->fail_at)return PCM_NO_HARDWARE;
    *value=f->rom[addr];return PCM_OK;
}
static void init(Fixture *f,Pcm *p)
{
    memset(f,0,sizeof(*f));memset(p,0,sizeof(*p));
    f->platform.context=f;f->platform.read8=read8;p->platform=&f->platform;
}
static unsigned target(unsigned state,unsigned proposed)
{
    unsigned n=state&7u;
    if(n==0)n=6;
    return 0xe57cu+4*(n>>1)+proposed;
}
static void contracts(void)
{
    Fixture f;Pcm p;uint8_t result;
    for(unsigned range=0;range<256;range++) {
        for(unsigned proposed=0;proposed<256;proposed++) {
            init(&f,&p);f.rom[0xa2]=(uint8_t)range;
            unsigned addr=target(range,proposed);
            f.rom[addr]=(uint8_t)(proposed^0x5au);
            result=0xc7;
            CHECK(pcm_transmission_gear_limit(&p,(uint8_t)proposed,&result)==PCM_OK);
            CHECK(f.reads==2 && f.addresses[0]==0x00a2 && f.addresses[1]==addr);
            unsigned bound=proposed^0x5au;
            CHECK(result==(bound<=proposed?bound:proposed));
        }
    }
    for(unsigned fail=1;fail<=2;fail++) {
        init(&f,&p);f.fail_at=fail;result=0xc7;
        CHECK(pcm_transmission_gear_limit(&p,17,&result)==PCM_NO_HARDWARE);
        CHECK(f.reads==fail && result==0xc7);
    }
    CHECK(pcm_transmission_gear_limit(NULL,1,&result)==PCM_BAD_CONFIGURATION);
    CHECK(pcm_transmission_gear_limit(&p,1,NULL)==PCM_BAD_CONFIGURATION);
    puts("E562 65536 range/candidate/memory index cases plus read-failure prefixes pass.");
}
int main(int argc,char **argv)
{
    if(argc==2 && strcmp(argv[1],"--contracts")==0) {
        contracts();return 0;
    }
    if(argc!=2)return 2;
    FILE*in=fopen(argv[1],"rb");if(!in)return 2;
    static uint8_t stock[65536];static Fixture f;Pcm p;
    int okay=fread(stock,1,sizeof(stock),in)==sizeof(stock);
    fclose(in);if(!okay)return 2;
    unsigned proposed,range,mod;
    while(scanf("%u %u %u",&proposed,&range,&mod)==3) {
        CHECK(proposed<256 && range<256 && mod<=256);
        init(&f,&p);memcpy(f.rom,stock,sizeof(stock));
        f.rom[0xa2]=(uint8_t)range;
        if(mod<256)f.rom[target(range,proposed)]=(uint8_t)mod;
        uint8_t value=0;
        PcmStatus status=pcm_transmission_gear_limit(&p,(uint8_t)proposed,&value);
        printf("{\"status\":%u,\"value\":%u,\"reads\":%u}\n",
             (unsigned)status,(unsigned)value,f.reads);
    }
    return ferror(stdin)?2:0;
}
