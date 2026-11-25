#include "hc11_irq_mailbox.h"
#include "hardware.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define CHECK(x) do {if(!(x)){ \
    fprintf(stderr,"hc11_irq_mailbox_test:%d: %s\n",__LINE__,#x);exit(1);\
} }while(0)

typedef struct {
    uint8_t regs[0x60],ram[0x400];
    unsigned writes;
    bool sabotage;
    volatile uint8_t *mailbox;
} Fake;

static PcmStatus fake_read(void *ctx,uint16_t a,uint8_t *out)
{
    Fake *f=ctx;
    if(out==NULL)return PCM_BAD_CONFIGURATION;
    if(a<0x0400u){*out=f->ram[a];return PCM_OK;}
    if(a>=0x3000u && a<0x3060u){*out=f->regs[a-0x3000u];return PCM_OK;}
    return PCM_NO_HARDWARE;
}
static PcmStatus fake_write(void *ctx,uint16_t a,uint8_t value)
{
    Fake *f=ctx;++f->writes;
    if(f->sabotage && f->mailbox!=NULL)
        f->mailbox[PCM_IRQ_MB_VECTOR_LO]=0xffu;
    if(a<0x0400u){f->ram[a]=value;return PCM_OK;}
    if(a>=0x3000u && a<0x3060u){f->regs[a-0x3000u]=value;return PCM_OK;}
    return PCM_NO_HARDWARE;
}
static PcmStatus fake_read16(void *ctx,uint16_t a,uint16_t *out)
{
    Fake *f=ctx;
    if(out==NULL)return PCM_BAD_CONFIGURATION;
    if(a<0x3000u||a>=0x305fu)return PCM_NO_HARDWARE;
    *out=(uint16_t)(((uint16_t)f->regs[a-0x3000u]<<8)|
                    f->regs[a-0x3000u+1u]);
    return PCM_OK;
}
static PcmStatus fake_write16(void *ctx,uint16_t a,uint16_t value)
{
    if(a<0x3000u||a>=0x305fu)return PCM_NO_HARDWARE;
    PcmStatus result=fake_write(ctx,a,(uint8_t)(value>>8));
    return result==PCM_OK?fake_write(ctx,(uint16_t)(a+1u),(uint8_t)value):result;
}
static void prepare(volatile uint8_t *m,uint16_t vector)
{
    for(unsigned i=0;i<PCM_IRQ_MB_SIZE;++i)m[i]=0u;
    m[PCM_IRQ_MB_VECTOR_HI]=(uint8_t)(vector>>8);
    m[PCM_IRQ_MB_VECTOR_LO]=(uint8_t)vector;
    m[PCM_IRQ_MB_CCR_HI]=0x03u;
    m[PCM_IRQ_MB_CCR_LO]=0xf7u;
    m[PCM_IRQ_MB_BUSY]=PCM_IRQ_MB_BUSY_TOKEN;
    m[PCM_IRQ_MB_PROOF]=PCM_IRQ_MB_PROOF_FRAME|PCM_IRQ_MB_PROOF_I_MASKED;
}
static void test_output_timers(void)
{
    const uint16_t vectors[]={0xffe0u,0xffe2u};
    for(unsigned i=0;i<2u;++i){
        Fake f={0};PcmPlatform platform={0};Pcm p={0};
        volatile uint8_t m[PCM_IRQ_MB_SIZE]={0};
        f.mailbox=m;platform.context=&f;platform.read8=fake_read;
        platform.write8=fake_write;platform.read16=fake_read16;
        platform.write16=fake_write16;p.platform=&platform;
        prepare(m,vectors[i]);
        CHECK(pcm_hc11_mailbox_dispatch(&p,m)==PCM_OK);
        CHECK(m[PCM_IRQ_MB_ACTION]==PCM_IRQ_MB_RTI_TOKEN&&m[PCM_IRQ_MB_STATUS]==PCM_OK);
        prepare(m,vectors[i]);
        platform.read16=NULL;
        CHECK(pcm_hc11_mailbox_dispatch(&p,m)==PCM_NO_HARDWARE);
        CHECK(m[PCM_IRQ_MB_ACTION]==0&&m[PCM_IRQ_MB_STATUS]==PCM_NO_HARDWARE);
    }
}
int main(void)
{
    test_output_timers();
    Fake f={0};PcmPlatform platform={0};Pcm p={0};
    volatile uint8_t m[PCM_IRQ_MB_SIZE]={0};
    f.mailbox=m;platform.context=&f;platform.read8=fake_read;
    platform.write8=fake_write;p.platform=&platform;
    prepare(m,0xffd8u); /* factory SPI body is empty, RTI after proper frame */
    CHECK(pcm_hc11_mailbox_dispatch(&p,m)==PCM_OK);
    CHECK(m[PCM_IRQ_MB_STATUS]==0 &&
          m[PCM_IRQ_MB_ACTION]==PCM_IRQ_MB_RTI_TOKEN && f.writes==0);
    m[PCM_IRQ_MB_ACTION]=PCM_IRQ_MB_RTI_TOKEN;
    m[PCM_IRQ_MB_PROOF]=0;
    CHECK(pcm_hc11_mailbox_dispatch(&p,m)==PCM_STACK_BOUNDARY);
    CHECK(m[PCM_IRQ_MB_ACTION]==0 &&
          m[PCM_IRQ_MB_STATUS]==PCM_STACK_BOUNDARY);

    prepare(m,0xffe4u); /* TOC3 cannot safely share this mailbox */
    CHECK(pcm_hc11_mailbox_dispatch(&p,m)==PCM_UNIMPLEMENTED);
    CHECK(m[PCM_IRQ_MB_ACTION]==0 &&
          m[PCM_IRQ_MB_STATUS]==PCM_UNIMPLEMENTED);
    prepare(m,0xfffeu); /* native reset never calls the C mailbox */
    CHECK(pcm_hc11_mailbox_dispatch(&p,m)==PCM_UNIMPLEMENTED);
    CHECK(m[PCM_IRQ_MB_ACTION]==0);
    prepare(m,0xfff4u); /* XIRQ needs separate saved-frame policy */
    CHECK(pcm_hc11_mailbox_dispatch(&p,m)==PCM_UNIMPLEMENTED);
    CHECK(m[PCM_IRQ_MB_ACTION]==0);

    prepare(m,0xffe6u); /* stock timer fallback is two byte writes */
    CHECK(pcm_hc11_mailbox_dispatch(&p,m)==PCM_OK);
    CHECK(m[PCM_IRQ_MB_ACTION]==PCM_IRQ_MB_RTI_TOKEN && f.writes==2);
    CHECK(f.regs[0x22]==0xa0u && f.regs[0x23]==0x5fu);

    prepare(m,0xffe6u);
    f.sabotage=true;
    CHECK(pcm_hc11_mailbox_dispatch(&p,m)==PCM_OK);
    CHECK(m[PCM_IRQ_MB_ACTION]==0); /* identity was changed in a callback */
    f.sabotage=false;

    prepare(m,0xffd8u);
    m[PCM_IRQ_MB_BUSY]=0u;
    CHECK(pcm_hc11_mailbox_dispatch(&p,m)==PCM_BAD_CONFIGURATION);
    CHECK(m[PCM_IRQ_MB_ACTION]==0);
    prepare(m,0xffd8u);
    m[PCM_IRQ_MB_CCR_LO]=0x80u;
    CHECK(pcm_hc11_mailbox_dispatch(&p,m)==PCM_STACK_BOUNDARY);
    CHECK(m[PCM_IRQ_MB_ACTION]==0);
    CHECK(pcm_hc11_mailbox_dispatch(NULL,m)==PCM_BAD_CONFIGURATION);
    CHECK(pcm_hc11_mailbox_dispatch(&p,NULL)==PCM_BAD_CONFIGURATION);

    /* Test the no-argument C symbol used by a future ASM11 JSR.
     * Reset binding must be explicit; host CRT defaults are irrelevant. */
    pcm_hc11_c_entry_reset();
    prepare(m,0xffd8u);
    pcm_hc11_c_entry();
    CHECK(m[PCM_IRQ_MB_ACTION]==0);
    CHECK(pcm_hc11_c_entry_bind(&p,m,false)==PCM_BAD_CONFIGURATION);
    CHECK(pcm_hc11_c_entry_bind(NULL,m,true)==PCM_BAD_CONFIGURATION);
    CHECK(pcm_hc11_c_entry_bind(&p,m,true)==PCM_OK);
    CHECK(pcm_hc11_c_entry_bind(&p,m,true)==PCM_BAD_CONFIGURATION);
    pcm_hc11_c_entry();
    CHECK(m[PCM_IRQ_MB_ACTION]==PCM_IRQ_MB_RTI_TOKEN &&
          m[PCM_IRQ_MB_STATUS]==PCM_OK);
    pcm_hc11_c_entry_reset();
    prepare(m,0xffd8u);
    pcm_hc11_c_entry();
    CHECK(m[PCM_IRQ_MB_ACTION]==0);
    puts("ASM11 ISR mailbox: RTI token, qualified frames, output timers, nesting and identity-change rejection passed");
    return 0;
}
