#include "interrupts.h"
#include "../system/system_internal.h"
/*FFF4 ->FC09..FC0F. Net stack effect of PULA/PSHA is a saved-CCR byte edit.
 * Read it after the cause RMW; mask bit40 is restored by target RTI. */
PcmStatus pcm_xirq_irq(Pcm *pcm,uint16_t saved_ccr_address)
{
    SYS_RUN(sys_update(pcm,0,0,4));
    uint8_t ccr;SYS_RUN(pcm_read8(pcm,saved_ccr_address,&ccr));
    return pcm_write8(pcm,saved_ccr_address,(uint8_t)(ccr|0x40u));
}
