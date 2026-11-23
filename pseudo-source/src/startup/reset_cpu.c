#include "startup.h"
#include "../system/system_internal.h"

/* 711C calls CC7C, then writes both ports and the startup board word. */
PcmStatus pcm_reset_cpu(Pcm *pcm)
{
    SYS_RUN(pcm_refresh_registers(pcm));
    SYS_RUN(pcm_write8(pcm, PCM_PORTA, 0));
    SYS_RUN(pcm_write8(pcm, PCM_PORTD, 0));
    return pcm_write16(pcm, PCM_BOARD_306E, 0x7fff);
}
