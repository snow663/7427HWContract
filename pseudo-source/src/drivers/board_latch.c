#include "board_io.h"
#include "hardware.h"
#define RUN(call) do { PcmStatus result=(call);if (result!=PCM_OK) return result; } while (0)
/* F3EE..F3FF, falling through F400. The JSR/RTS gap is11 nominal E cycles;
 * target call overhead and peripheral settling remain separate validation. */
PcmStatus pcm_board_latch(Pcm *pcm)
{
    RUN(pcm_mask_irq(pcm,true));
    uint16_t command;
    RUN(pcm_read16(pcm,PCM_BOARD_CONTROL,&command));
    RUN(pcm_delay_cycles(pcm,11));
    if (pcm->runtime.service_output_mirror) command &= (uint16_t)~8u;
    else command |= 8u;
    RUN(pcm_write16(pcm,PCM_BOARD_CONTROL,command));
    return pcm_board_ports(pcm);
}
