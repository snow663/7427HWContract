#ifndef PCM_HC11_IRQ_MAILBOX_H
#define PCM_HC11_IRQ_MAILBOX_H
#include "hc11_vector_contract.h"

/* Exact eight byte offsets in the ASM11 hal_ram.inc allocation. */
enum {
    PCM_IRQ_MB_VECTOR_HI=0, PCM_IRQ_MB_VECTOR_LO=1,
    PCM_IRQ_MB_CCR_HI=2, PCM_IRQ_MB_CCR_LO=3,
    PCM_IRQ_MB_STATUS=4, PCM_IRQ_MB_ACTION=5,
    PCM_IRQ_MB_BUSY=6, PCM_IRQ_MB_PROOF=7,
    PCM_IRQ_MB_SIZE=8,
    PCM_IRQ_MB_RTI_TOKEN=0xa5,
    PCM_IRQ_MB_BUSY_TOKEN=0xa5,
    PCM_IRQ_MB_PROOF_FRAME=1, PCM_IRQ_MB_PROOF_I_MASKED=2,
    PCM_IRQ_MB_PROOF_TOC3=4, PCM_IRQ_MB_PROOF_XIRQ=8
};

/* Called by a future compiler-specific no-argument RTS thunk.
 * NOT called directly by ASM11: its args are compiler ABI dependent. */
PcmStatus pcm_hc11_mailbox_dispatch(Pcm *pcm,volatile uint8_t *mailbox);
#endif
