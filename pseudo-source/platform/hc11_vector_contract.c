#include "hc11_vector_contract.h"
#include "interrupts.h"
#include "hardware.h"
#include "scheduler.h"
#include "serial.h"

#define PCM_HC11_VECTOR(addr, label, pc, role) {addr, #label, pc, PCM_HC11_KIND_##role},
static const PcmHc11VectorInfo vector_map[] = {
#include "hc11_vector_map.def"
};
#undef PCM_HC11_VECTOR

const PcmHc11VectorInfo *pcm_hc11_vector_info(uint16_t address)
{
    if (address<0xffd6u || (address&1u)!=0u) return NULL;
    unsigned index=((unsigned)address-0xffd6u)/2u;
    return index<sizeof(vector_map)/sizeof(vector_map[0]) &&
           vector_map[index].vector_address==address ? &vector_map[index] : NULL;
}

PcmStatus pcm_hc11_vector_dispatch(Pcm *pcm,uint16_t vector,
                                   const PcmHc11NativeFrame *frame,
                                   PcmHc11NativeAction *action)
{
    if(action==NULL)return PCM_BAD_CONFIGURATION;
    *action=PCM_HC11_NO_NATIVE_RETURN;
    const PcmHc11VectorInfo *info=pcm_hc11_vector_info(vector);
    if(info==NULL||pcm==NULL)return PCM_BAD_CONFIGURATION;

    /* Reset-class exception entry cannot trust a C struct or the stack. */
    if(info->kind==PCM_HC11_KIND_EXTERNAL_RESET ||
       info->kind==PCM_HC11_KIND_COP_RESET) {
        *action=PCM_HC11_NATIVE_RESET_REQUIRED;
        return PCM_RESET_BOUNDARY;
    }
    if(info->kind==PCM_HC11_KIND_CLOCK_FAILURE) {
        *action=PCM_HC11_NATIVE_HALT_REQUIRED;
        return PCM_HALT_BOUNDARY;
    }
    if(frame==NULL||!frame->frame_verified||!frame->entry_interrupts_masked)
        return PCM_STACK_BOUNDARY;
    if(info->kind==PCM_HC11_KIND_TOC3 &&
       (!frame->toc3_stack_contract_verified||pcm->platform==NULL||
       (pcm->platform->capture_timer_stack_x==NULL &&
        pcm->platform->check_stack==NULL)))return PCM_STACK_BOUNDARY;
    if(info->kind==PCM_HC11_KIND_XIRQ &&
       (!frame->xirq_saved_ccr_verified||
        frame->xirq_saved_ccr_address<0x03b0u||
        frame->xirq_saved_ccr_address>0x03ffu))return PCM_STACK_BOUNDARY;

    PcmStatus status=PCM_UNIMPLEMENTED;
    switch(info->kind) {
      case PCM_HC11_KIND_SCI:status=pcm_sci_irq(pcm);break;
      case PCM_HC11_KIND_SPI:status=pcm_spi_irq(pcm);break;
      case PCM_HC11_KIND_OVERFLOW:status=pcm_overflow_fallback_irq(pcm);break;
      case PCM_HC11_KIND_TIMER_FALLBACK:status=pcm_timer_fallback_irq(pcm);break;
      case PCM_HC11_KIND_OC1:status=pcm_oc1_irq(pcm);break;
      case PCM_HC11_KIND_TOC5:status=pcm_toc5_irq(pcm);break;
      case PCM_HC11_KIND_TOC4:status=pcm_toc4_irq(pcm);break;
      case PCM_HC11_KIND_TOC3:status=pcm_periodic_irq(pcm);break;
      case PCM_HC11_KIND_REF:status=pcm_reference_irq(pcm);break;
      case PCM_HC11_KIND_XIRQ:
        status=pcm_xirq_irq(pcm,frame->xirq_saved_ccr_address);break;
      case PCM_HC11_KIND_SWI:status=pcm_swi_irq(pcm);break;
      case PCM_HC11_KIND_ILLEGAL:status=pcm_illegal_trap(pcm);break;
      case PCM_HC11_KIND_COP_RESET:
      case PCM_HC11_KIND_CLOCK_FAILURE:
      case PCM_HC11_KIND_EXTERNAL_RESET:
        return PCM_BAD_CONFIGURATION;
    }
    if(status==PCM_OK) *action=PCM_HC11_NATIVE_RTI_REQUIRED;
    else if(status==PCM_STACK_RECOVERY_BOUNDARY)
        *action=PCM_HC11_NATIVE_STACK_RECOVERY;
    else if(status==PCM_RESET_BOUNDARY)
        *action=PCM_HC11_NATIVE_RESET_REQUIRED;
    else if(status==PCM_HALT_BOUNDARY)
        *action=PCM_HC11_NATIVE_HALT_REQUIRED;
    /* Every other result is NOT a safe RTI permission. */
    return status;
}
