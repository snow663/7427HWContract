#include "hc11_irq_mailbox.h"

/* Software-side end of the ASM11 IRQ mailbox; no target C ABI assumed. */
PcmStatus pcm_hc11_mailbox_dispatch(Pcm *pcm,volatile uint8_t *mb)
{
    if(mb==NULL)return PCM_BAD_CONFIGURATION;
    mb[PCM_IRQ_MB_ACTION]=0u;
    mb[PCM_IRQ_MB_STATUS]=(uint8_t)PCM_BAD_CONFIGURATION;
    if(pcm==NULL || mb[PCM_IRQ_MB_BUSY]!=PCM_IRQ_MB_BUSY_TOKEN)
        return PCM_BAD_CONFIGURATION;

    uint16_t vector=(uint16_t)(((uint16_t)mb[PCM_IRQ_MB_VECTOR_HI]<<8) |
                               mb[PCM_IRQ_MB_VECTOR_LO]);
    uint16_t ccr=(uint16_t)(((uint16_t)mb[PCM_IRQ_MB_CCR_HI]<<8) |
                            mb[PCM_IRQ_MB_CCR_LO]);
    uint8_t proof=mb[PCM_IRQ_MB_PROOF];
    const PcmHc11VectorInfo *info=pcm_hc11_vector_info(vector);

    /* The common mailbox is non-reentrant. TOC3 can unmask inside its
     * body: it and XIRQ/traps/reset are not allowed through this adapter. */
    if(info==NULL || info->kind==PCM_HC11_KIND_TOC3 ||
       info->kind==PCM_HC11_KIND_XIRQ ||
       info->kind==PCM_HC11_KIND_COP_RESET ||
       info->kind==PCM_HC11_KIND_EXTERNAL_RESET ||
       info->kind==PCM_HC11_KIND_CLOCK_FAILURE ||
       info->kind==PCM_HC11_KIND_SWI ||
       info->kind==PCM_HC11_KIND_ILLEGAL)
        return PCM_UNIMPLEMENTED;

    if((proof & (PCM_IRQ_MB_PROOF_FRAME|PCM_IRQ_MB_PROOF_I_MASKED))!=
       (PCM_IRQ_MB_PROOF_FRAME|PCM_IRQ_MB_PROOF_I_MASKED) ||
       (proof & (PCM_IRQ_MB_PROOF_TOC3|PCM_IRQ_MB_PROOF_XIRQ))!=0u ||
       ccr<0x03b0u || ccr>0x03f7u)
        return PCM_STACK_BOUNDARY;

    PcmHc11NativeFrame frame={0};
    frame.frame_verified=true;
    frame.entry_interrupts_masked=true;
    PcmHc11NativeAction action=PCM_HC11_NO_NATIVE_RETURN;
    PcmStatus status=pcm_hc11_vector_dispatch(pcm,vector,&frame,&action);
    mb[PCM_IRQ_MB_STATUS]=(uint8_t)status;
    if(status==PCM_OK && action==PCM_HC11_NATIVE_RTI_REQUIRED &&
       mb[PCM_IRQ_MB_BUSY]==PCM_IRQ_MB_BUSY_TOKEN &&
       mb[PCM_IRQ_MB_PROOF]==proof &&
       mb[PCM_IRQ_MB_VECTOR_HI]==(uint8_t)(vector>>8) &&
       mb[PCM_IRQ_MB_VECTOR_LO]==(uint8_t)vector &&
       mb[PCM_IRQ_MB_CCR_HI]==(uint8_t)(ccr>>8) &&
       mb[PCM_IRQ_MB_CCR_LO]==(uint8_t)ccr)
        mb[PCM_IRQ_MB_ACTION]=PCM_IRQ_MB_RTI_TOKEN;
    return status;
}
