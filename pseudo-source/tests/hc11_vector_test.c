#include "hc11_vector_contract.h"
#include "hardware.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define CHECK(x) do { if(!(x)){ \
    fprintf(stderr,"hc11_vector_test:%d: %s\n",__LINE__,#x);exit(1); \
} } while(0)

typedef struct {
    uint8_t ram[0x400], registers[0x60];
    unsigned reads,writes;
    uint16_t address[10];
    uint8_t values[10];
} Fixture;
static PcmStatus fake_read(void *ctx,uint16_t a,uint8_t *v)
{
    Fixture *f=ctx;
    if(v==NULL)return PCM_BAD_CONFIGURATION;
    ++f->reads;
    if(a<0x400u){*v=f->ram[a];return PCM_OK;}
    if(a>=0x3000u&&a<0x3060u){*v=f->registers[a-0x3000u];return PCM_OK;}
    return PCM_NO_HARDWARE;
}
static PcmStatus fake_write(void *ctx,uint16_t a,uint8_t v)
{
    Fixture *f=ctx;
    if(f->writes<10u){f->address[f->writes]=a;f->values[f->writes]=v;}
    ++f->writes;
    if(a<0x400u){f->ram[a]=v;return PCM_OK;}
    if(a>=0x3000u&&a<0x3060u){f->registers[a-0x3000u]=v;return PCM_OK;}
    return PCM_NO_HARDWARE;
}
static void test_inventory(void)
{
    for(unsigned i=0;i<21u;++i){
        uint16_t a=(uint16_t)(0xffd6u+2u*i);
        const PcmHc11VectorInfo *v=pcm_hc11_vector_info(a);
        CHECK(v!=NULL&&v->vector_address==a);
        CHECK(v->factory_handler_address>=0x4000u);
        CHECK(v->source_name!=NULL&&v->source_name[0]!='\0');
    }
    CHECK(pcm_hc11_vector_info(0xffd4u)==NULL);
    CHECK(pcm_hc11_vector_info(0xffd7u)==NULL);
    CHECK(pcm_hc11_vector_info(0x0000u)==NULL);
}
static void test_entry_requirements(void)
{
    Fixture f={0};PcmPlatform platform={0};Pcm p={0};
    platform.context=&f;platform.read8=fake_read;platform.write8=fake_write;
    p.platform=&platform;
    PcmHc11NativeAction action=PCM_HC11_NATIVE_RTI_REQUIRED;
    PcmHc11NativeFrame frame={0};
    CHECK(pcm_hc11_vector_dispatch(&p,0xffd6u,&frame,&action)==PCM_STACK_BOUNDARY);
    CHECK(action==PCM_HC11_NO_NATIVE_RETURN&&f.reads==0&&f.writes==0);
    frame.frame_verified=true;frame.entry_interrupts_masked=true;
    CHECK(pcm_hc11_vector_dispatch(&p,0xffe0u,&frame,&action)==PCM_UNIMPLEMENTED);
    CHECK(action==PCM_HC11_NO_NATIVE_RETURN);
    CHECK(pcm_hc11_vector_dispatch(&p,0xffe2u,&frame,&action)==PCM_UNIMPLEMENTED);
    CHECK(pcm_hc11_vector_dispatch(&p,0xffe4u,&frame,&action)==PCM_STACK_BOUNDARY);
    CHECK(pcm_hc11_vector_dispatch(&p,0xfff4u,&frame,&action)==PCM_STACK_BOUNDARY);
    CHECK(pcm_hc11_vector_dispatch(&p,0xffffu,&frame,&action)==PCM_BAD_CONFIGURATION);
    CHECK(pcm_hc11_vector_dispatch(&p,0xfffeu,NULL,&action)==PCM_RESET_BOUNDARY);
    CHECK(action==PCM_HC11_NATIVE_RESET_REQUIRED);
    CHECK(pcm_hc11_vector_dispatch(&p,0xfffau,NULL,&action)==PCM_RESET_BOUNDARY);
    CHECK(action==PCM_HC11_NATIVE_RESET_REQUIRED);
    CHECK(pcm_hc11_vector_dispatch(&p,0xfffcu,NULL,&action)==PCM_HALT_BOUNDARY);
    CHECK(action==PCM_HC11_NATIVE_HALT_REQUIRED);
    CHECK(pcm_hc11_vector_dispatch(&p,0xffd6u,NULL,NULL)==PCM_BAD_CONFIGURATION);
    CHECK(f.reads==0&&f.writes==0);
}
static void test_resident_leaves(void)
{
    Fixture f={0};PcmPlatform platform={0};Pcm p={0};
    platform.context=&f;platform.read8=fake_read;platform.write8=fake_write;
    p.platform=&platform;
    PcmHc11NativeFrame frame={0};
    frame.frame_verified=true;frame.entry_interrupts_masked=true;
    PcmHc11NativeAction action;
    CHECK(pcm_hc11_vector_dispatch(&p,0xffd8u,&frame,&action)==PCM_OK);
    CHECK(action==PCM_HC11_NATIVE_RTI_REQUIRED&&f.writes==0&&f.reads==0);
    CHECK(pcm_hc11_vector_dispatch(&p,0xffe6u,&frame,&action)==PCM_OK);
    CHECK(action==PCM_HC11_NATIVE_RTI_REQUIRED&&f.writes==2);
    CHECK(f.address[0]==PCM_TMSK1&&f.values[0]==0xa0u);
    CHECK(f.address[1]==PCM_TFLG1&&f.values[1]==0x5fu);
    CHECK(pcm_hc11_vector_dispatch(&p,0xffdeu,&frame,&action)==PCM_OK);
    CHECK(f.writes==4&&f.address[2]==0x3024u&&f.address[3]==0x3025u);
    frame.xirq_saved_ccr_verified=true;
    frame.xirq_saved_ccr_address=0x03f8u;
    f.ram[0x03f8u]=0x20u;
    CHECK(pcm_hc11_vector_dispatch(&p,0xfff4u,&frame,&action)==PCM_OK);
    CHECK(action==PCM_HC11_NATIVE_RTI_REQUIRED);
    CHECK((f.ram[0x03f8u]&0x40u)!=0);
}
int main(void)
{
    test_inventory();test_entry_requirements();test_resident_leaves();
    puts("HC11 vector bridge: 21 source vectors, entry guards, fallback and saved-CCR tests passed");
    return 0;
}
