#ifndef PCM_SYSTEM_INTERNAL_H
#define PCM_SYSTEM_INTERNAL_H
#include "system.h"
#include "serial.h"
#include "hardware.h"
#define SYS_RUN(call) do { PcmStatus result=(call);if (result!=PCM_OK) return result; } while (0)
/* Logical RAM must be bound to its canonical named owners by the provider. */
static inline PcmStatus sys_update(Pcm *pcm,uint16_t address,uint8_t clear,uint8_t set)
{
    uint8_t value;SYS_RUN(pcm_serial_memory_read8(pcm,address,&value));
    return pcm_serial_memory_write8(pcm,address,(uint8_t)((value&~clear)|set));
}
#endif
