#include "hc11_irq_mailbox.h"

/* Native/host C-side handler with a zero-argument, ordinary C return.
 * Unlike pcm_hc11_mailbox_dispatch, the ASM11 gateway can JSR this
 * function without passing compiler-specific arguments. A real compiler
 * map/S19 inspection must still prove its symbol, RTS, stack balance
 * and DATA/BSS initialization before the ROM entry word is rebound.
 *
 * These pointers have no assumed fixed target addresses. They are set by
 * the native reset/init code while interrupts are masked.
 */
static Pcm *native_pcm;
static volatile uint8_t *native_mailbox;
static bool native_ready;

void pcm_hc11_c_entry_reset(void)
{
    native_ready=false;
    native_pcm=NULL;
    native_mailbox=NULL;
}

PcmStatus pcm_hc11_c_entry_bind(Pcm *pcm,volatile uint8_t *mailbox,
                                bool interrupts_masked)
{
    if(!interrupts_masked||pcm==NULL||mailbox==NULL||native_ready)
        return PCM_BAD_CONFIGURATION;
    native_pcm=pcm;
    native_mailbox=mailbox;
    native_ready=true;
    return PCM_OK;
}

void pcm_hc11_c_entry(void)
{
    if(!native_ready||native_pcm==NULL||native_mailbox==NULL)
        return; /* gateway action was cleared before the call */
    (void)pcm_hc11_mailbox_dispatch(native_pcm,native_mailbox);
}
