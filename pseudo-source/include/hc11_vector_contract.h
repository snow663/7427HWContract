#ifndef PCM_HC11_VECTOR_CONTRACT_H
#define PCM_HC11_VECTOR_CONTRACT_H
#include "pcm.h"

/* Host-checkable C boundary. Native vector fetch, CCR/SP, saved frame,
 * compiler calling convention, and RTI belong to the HC11 assembly shim. */
typedef enum {
    PCM_HC11_KIND_SCI, PCM_HC11_KIND_SPI, PCM_HC11_KIND_OVERFLOW,
    PCM_HC11_KIND_UNBOUND_OUTPUT_TIMER, PCM_HC11_KIND_TOC3,
    PCM_HC11_KIND_TIMER_FALLBACK, PCM_HC11_KIND_OC1, PCM_HC11_KIND_REF,
    PCM_HC11_KIND_XIRQ, PCM_HC11_KIND_SWI, PCM_HC11_KIND_ILLEGAL,
    PCM_HC11_KIND_COP_RESET, PCM_HC11_KIND_CLOCK_FAILURE,
    PCM_HC11_KIND_EXTERNAL_RESET
} PcmHc11VectorKind;

typedef struct {
    uint16_t vector_address;
    const char *source_name;
    uint16_t factory_handler_address;
    PcmHc11VectorKind kind;
} PcmHc11VectorInfo;

typedef enum {
    PCM_HC11_NO_NATIVE_RETURN,
    PCM_HC11_NATIVE_RTI_REQUIRED,
    PCM_HC11_NATIVE_STACK_RECOVERY,
    PCM_HC11_NATIVE_RESET_REQUIRED,
    PCM_HC11_NATIVE_HALT_REQUIRED
} PcmHc11NativeAction;

typedef struct {
    /* Only a native wrapper can assert these, not portable C. */
    bool frame_verified;
    bool entry_interrupts_masked;
    bool toc3_stack_contract_verified;
    bool xirq_saved_ccr_verified;
    uint16_t xirq_saved_ccr_address;
} PcmHc11NativeFrame;

const PcmHc11VectorInfo *pcm_hc11_vector_info(uint16_t vector_address);
PcmStatus pcm_hc11_vector_dispatch(Pcm *pcm, uint16_t vector_address,
                                   const PcmHc11NativeFrame *frame,
                                   PcmHc11NativeAction *action);
#endif
