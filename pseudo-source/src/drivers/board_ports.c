#include "board_io.h"
#include "hardware.h"
#define RUN(call) do { PcmStatus result=(call);if (result!=PCM_OK) return result; } while (0)
/* F400..F41F.3060 receives only004B&90; RAM004B is reconstructed afterward.
 * The input sample and output request remain local across the peripheral write. */
PcmStatus pcm_board_ports(Pcm *pcm)
{
    uint8_t sample;
    RUN(pcm_read8(pcm,PCM_BOARD_3060,&sample));
    sample &= 0x6fu;
    uint8_t outputs=(pcm->spark.output_request?0x10u:0u) | (pcm->iac.kicker_request?0x80u:0u);
    RUN(pcm_write8(pcm,PCM_BOARD_3060,outputs));
    uint8_t merged=(uint8_t)(sample+outputs);
    pcm->io.output_context=merged&0x6fu;
    pcm->spark.output_request=(merged&0x10u)!=0;
    pcm->iac.kicker_request=(merged&0x80u)!=0;
    RUN(pcm_write8(pcm,PCM_BOARD_3062,pcm->transmission.output_shadow));
    RUN(pcm_read8(pcm,PCM_BOARD_3064,&sample));
    pcm->iac.input_shadow=sample;
    RUN(pcm_write8(pcm,PCM_BOARD_3067,pcm->io.auxiliary_output));
    return pcm_mask_irq(pcm,false);
}
