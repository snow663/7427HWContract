#include "hc11_execution.h"
#include "hardware.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define CHECK(c) do {if(!(c)){fprintf(stderr,"HC11 execution %d: %s\n",__LINE__,#c);exit(1);} }while(0)

typedef struct {
    uint8_t memory[0x10000];
    unsigned reads,writes;
    bool irq_masked;
    uint16_t captured_stack_x;
    unsigned stack_captures;
} Fixture;
static PcmStatus read8(void *p,uint16_t a,uint8_t *v)
{
    if(v==NULL)return PCM_BAD_CONFIGURATION;
    Fixture *f=p; ++f->reads;*v=f->memory[a];return PCM_OK;
}
static PcmStatus read16(void *p,uint16_t a,uint16_t *v)
{
    if(v==NULL || a==0xffffu)return PCM_BAD_CONFIGURATION;
    Fixture *f=p;++f->reads;
    *v=(uint16_t)(((uint16_t)f->memory[a]<<8)|f->memory[a+1u]);
    return PCM_OK;
}
static PcmStatus write8(void *p,uint16_t a,uint8_t v)
{
    Fixture *f=p;++f->writes;f->memory[a]=v;return PCM_OK;
}
static PcmStatus write16(void *p,uint16_t a,uint16_t v)
{
    if(a==0xffffu)return PCM_BAD_CONFIGURATION;
    Fixture *f=p;++f->writes;f->memory[a]=(uint8_t)(v>>8);
    f->memory[a+1u]=(uint8_t)v;return PCM_OK;
}
static PcmStatus mask_irq(void *p,bool masked)
{
    ((Fixture *)p)->irq_masked=masked;
    return PCM_OK;
}
static PcmStatus capture_timer_stack_x(void *p,uint16_t *out)
{
    if(out==NULL)return PCM_BAD_CONFIGURATION;
    Fixture *f=p;
    ++f->stack_captures;
    *out=f->captured_stack_x;
    return PCM_OK;
}

int main(void)
{
    static Fixture f;
    PcmPlatform platform={0};
    platform.context=&f;
    platform.read8=read8;platform.read16=read16;
    platform.write8=write8;platform.write16=write16;
    platform.mask_irq=mask_irq;
    PcmCalibration calibration={0};
    calibration.format_version=1;
    calibration.recurring_compare_counts=15000;
    calibration.first_compare_counts=14000;
    Pcm pcm={0};
    pcm.platform=&platform;pcm.calibration=&calibration;
    volatile uint8_t mailbox[PCM_IRQ_MB_SIZE]={0};
    PcmHc11Execution exec={0};
    PcmHc11BootWitness proof={
        .stack_pointer=0x03ff,
        .register_base=0x3000,
        .reset_prelude_complete=true,
        .irq_masked=true,
        .c_state_initialized=true,
        .actuator_permissions_off=true,
    };
    CHECK(pcm_hc11_exec_attach(&exec,&pcm,mailbox,NULL)==PCM_BAD_CONFIGURATION);
    CHECK(exec.phase==PCM_HC11_EXEC_OFFLINE);
    proof.irq_masked=false;
    CHECK(pcm_hc11_exec_attach(&exec,&pcm,mailbox,&proof)==PCM_BAD_CONFIGURATION);
    proof.irq_masked=true;
    proof.register_base=0x1000;
    CHECK(pcm_hc11_exec_attach(&exec,&pcm,mailbox,&proof)==PCM_BAD_CONFIGURATION);
    proof.register_base=0x3000;
    CHECK(pcm_hc11_exec_attach(&exec,&pcm,mailbox,&proof)==PCM_OK);
    CHECK(exec.phase==PCM_HC11_EXEC_READY);
    CHECK(pcm_hc11_exec_attach(&exec,&pcm,mailbox,&proof)==PCM_BAD_CONFIGURATION);

    /* Stock $746C-$74D0 eventually requests a native WAI boundary. */
    CHECK(pcm_hc11_exec_background(&exec)==PCM_BACKGROUND_WAIT_BOUNDARY);
    CHECK(exec.phase==PCM_HC11_EXEC_WAITING && exec.foreground_passes==1);
    CHECK(!f.irq_masked); /* background routine explicitly opened IRQs */
    CHECK(pcm_hc11_exec_background(&exec)==PCM_BAD_CONFIGURATION);

    PcmHc11NativeFrame frame={0};
    frame.frame_verified=true;
    frame.entry_interrupts_masked=true;
    PcmHc11NativeAction action=PCM_HC11_NO_NATIVE_RETURN;
    CHECK(pcm_hc11_exec_interrupt(&exec,0xffd8u,&frame,&action)==PCM_OK);
    CHECK(exec.phase==PCM_HC11_EXEC_READY && exec.interrupt_returns==1);
    CHECK(action==PCM_HC11_NATIVE_RTI_REQUIRED && exec.last_vector==0xffd8u);

    /* Both resident output leaves authorize RTI only after completed I/O. */
    CHECK(pcm_hc11_exec_interrupt(&exec,0xffe2u,&frame,&action)==PCM_OK);
    CHECK(exec.phase==PCM_HC11_EXEC_READY&&exec.interrupt_returns==2);
    CHECK(action==PCM_HC11_NATIVE_RTI_REQUIRED&&exec.last_vector==0xffe2u);
    platform.read16=NULL;
    CHECK(pcm_hc11_exec_interrupt(&exec,0xffe0u,&frame,&action)==PCM_NO_HARDWARE);
    CHECK(exec.phase==PCM_HC11_EXEC_TRAPPED);
    CHECK(action==PCM_HC11_NO_NATIVE_RETURN);
    CHECK(exec.interrupt_returns==2);
    CHECK(pcm_hc11_exec_background(&exec)==PCM_BAD_CONFIGURATION);
    platform.read16=read16;

    pcm_hc11_exec_reset(&exec);
    CHECK(exec.phase==PCM_HC11_EXEC_OFFLINE);
    CHECK(pcm_hc11_exec_attach(&exec,&pcm,mailbox,&proof)==PCM_OK);
    frame.frame_verified=false;
    CHECK(pcm_hc11_exec_interrupt(&exec,0xffd8u,&frame,&action)==PCM_STACK_BOUNDARY);
    CHECK(exec.phase==PCM_HC11_EXEC_TRAPPED);
    CHECK(action==PCM_HC11_NO_NATIVE_RETURN);
    pcm_hc11_exec_reset(&exec);
    CHECK(pcm_hc11_exec_attach(&exec,&pcm,mailbox,&proof)==PCM_OK);
    CHECK(pcm_hc11_exec_interrupt(&exec,0xfffeu,NULL,&action)==PCM_RESET_BOUNDARY);
    CHECK(action==PCM_HC11_NATIVE_RESET_REQUIRED);
    CHECK(exec.phase==PCM_HC11_EXEC_OFFLINE);

    /* TOC3 is the real scheduler heartbeat. Its stock $7959-$7979 guard
     * demands a fresh native stack recovery (LDS #$03F6) when the captured
     * X is outside the permitted saved-frame interval. It must not RTI. */
    pcm_hc11_exec_reset(&exec);
    platform.capture_timer_stack_x=capture_timer_stack_x;
    f.captured_stack_x=0x03a0u;
    CHECK(pcm_hc11_exec_attach(&exec,&pcm,mailbox,&proof)==PCM_OK);
    frame.frame_verified=true;
    frame.toc3_stack_contract_verified=true;
    CHECK(pcm_hc11_exec_interrupt(&exec,0xffe4u,&frame,&action)==
          PCM_STACK_RECOVERY_BOUNDARY);
    CHECK(exec.phase==PCM_HC11_EXEC_RECOVERY_REQUIRED);
    CHECK(action==PCM_HC11_NATIVE_STACK_RECOVERY);
    CHECK(exec.last_vector==0xffe4u && exec.interrupt_returns==0);
    CHECK(f.stack_captures==1);
    CHECK(pcm.scheduler.timer_seen && f.memory[PCM_TFLG1]==0x20u);
    CHECK((f.memory[0x003au]&8u)!=0u);
    CHECK(f.memory[PCM_TOC3]==(uint8_t)(15000u>>8));
    CHECK(f.memory[PCM_TOC3+1u]==(uint8_t)15000u);
    CHECK(pcm_hc11_exec_background(&exec)==PCM_BAD_CONFIGURATION);
    CHECK(pcm_hc11_exec_interrupt(&exec,0xffd8u,&frame,&action)==
          PCM_BAD_CONFIGURATION);

    puts("HC11 source execution: boot admission, WAI wait, IRQ/RTI action, trap and reset boundaries passed.");
    return 0;
}
