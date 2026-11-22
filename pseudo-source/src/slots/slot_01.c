#include "scheduler.h"
#include "board_io.h"
#include "control.h"
#include "../system/system_internal.h"
/* Reference 7AAD, table word 7A87.
 * Stock body: 7AAD:C583;7AB0:C668;7AB3:ADAA
 * All three resident callees run in their source order. */
PcmStatus pcm_slot_01(Pcm *pcm)
{
    SYS_RUN(pcm_baro_input(pcm));SYS_RUN(pcm_transmission_baro(pcm));
    return pcm_tcc_nonelectronic(pcm);
}
