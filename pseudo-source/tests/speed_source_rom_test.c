/* Replays source $C668 using the verified full BMHM byte view.
 * Host fixture reads/writes the original logical addresses, not a
 * replacement PCM hardware memory model. */
#include "board_io.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define CHECK(x) do {if(!(x)){fprintf(stderr,"speed source fixture:%d: %s\n",__LINE__,#x);exit(3);}}while(0)
typedef struct {
    PcmPlatform io;
    uint8_t image[65536];
    unsigned reads,writes,fail_at,ops;
} Fixture;
static PcmStatus read8(void *ctx,uint16_t a,uint8_t *out)
{
    Fixture *f=ctx;if(++f->ops==f->fail_at)return PCM_NO_HARDWARE;
    ++f->reads;*out=f->image[a];return PCM_OK;
}
static PcmStatus read16(void *ctx,uint16_t a,uint16_t *out)
{
    Fixture *f=ctx;if(++f->ops==f->fail_at)return PCM_NO_HARDWARE;
    ++f->reads;*out=(uint16_t)((uint16_t)f->image[a]<<8|f->image[(uint16_t)(a+1u)]);
    return PCM_OK;
}
static PcmStatus write16(void *ctx,uint16_t a,uint16_t value)
{
    Fixture *f=ctx;if(++f->ops==f->fail_at)return PCM_NO_HARDWARE;
    ++f->writes;f->image[a]=(uint8_t)(value>>8);
    f->image[(uint16_t)(a+1u)]=(uint8_t)value;return PCM_OK;
}
int main(int argc,char **argv)
{
    if(argc!=2)return 2;
    static uint8_t image[65536];static Fixture f;Pcm pcm;
    FILE *file=fopen(argv[1],"rb");if(!file)return 2;
    int complete=fread(image,1,sizeof(image),file)==sizeof(image);
    fclose(file);if(!complete)return 2;
    unsigned count;
    while(scanf("%u",&count)==1) {
        CHECK(count<1024);
        memset(&f,0,sizeof(f));memset(&pcm,0,sizeof(pcm));
        memcpy(f.image,image,sizeof(image));
        f.io.context=&f;f.io.read8=read8;f.io.read16=read16;
        f.io.write16=write16;pcm.platform=&f.io;
        for(unsigned k=0;k<count;++k) {
            unsigned a,v;CHECK(scanf("%u %u",&a,&v)==2);
            CHECK(a<65536 && v<256);
            f.image[a]=(uint8_t)v;
        }
        f.fail_at=f.image[0x907];
        PcmStatus status=pcm_speed_source(&pcm);
        printf("{\"status\":%u,\"word\":%u,\"reads\":%u,\"writes\":%u}\n",
            (unsigned)status,(unsigned)((unsigned)f.image[0xac]*256+f.image[0xad]),
            f.reads,f.writes);
    }
    return ferror(stdin)?2:0;
}
