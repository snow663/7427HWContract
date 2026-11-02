#include "serial_internal.h"
/*F637/FA3B/F813 word sequences. Low3FFD.2 is the SCI driver, distinct
 * from high3FFC.2 fuel triggering. The caller owns the IRQ-mask precondition. */
PcmStatus pcm_serial_driver(Pcm *pcm,bool enabled)
{
    uint16_t control;SER_RUN(pcm_read16(pcm,PCM_BOARD_CONTROL,&control));
    SER_RUN(pcm_delay_cycles(pcm,11));
    control=enabled ? (uint16_t)(control|4u) : (uint16_t)(control&0xfffbu);
    return pcm_write16(pcm,PCM_BOARD_CONTROL,control);
}
