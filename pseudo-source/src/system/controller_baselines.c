#include "system_internal.h"
/* 74D3..74E9: two separate board commands, with the F3ED call/return delay. */
PcmStatus pcm_controller_baselines(Pcm *pcm)
{
    SYS_RUN(pcm_write16(pcm,0x3fcc,0xd000));
    if (pcm->platform==NULL || pcm->platform->delay_cycles==NULL) return PCM_NO_HARDWARE;
    SYS_RUN(pcm->platform->delay_cycles(pcm->platform->context,11));
    SYS_RUN(pcm_write16(pcm,0x3fea,0xdfff));
    SYS_RUN(pcm->platform->delay_cycles(pcm->platform->context,11));
    return pcm_write8(pcm,0x00d9,1);
}
