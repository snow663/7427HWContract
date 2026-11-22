#ifndef PCM_DIAGNOSTIC_INTERNAL_H
#define PCM_DIAGNOSTIC_INTERNAL_H
#include "control.h"
#include "../system/system_internal.h"
/* Keep each operand transaction and RMW fresh. Shared diagnostic RAM must
 * bind to the same canonical owners used by transmission, fuel and spark. */
#define DG8(address,out) SYS_RUN(pcm_serial_memory_read8(pcm,(address),&(out)))
#define DG16(address,out) SYS_RUN(pcm_read16(pcm,(address),&(out)))
#define DG_SET(address,mask) SYS_RUN(sys_update(pcm,(address),0,(mask)))
#define DG_CLEAR(address,mask) SYS_RUN(sys_update(pcm,(address),(mask),0))
static inline int32_t dg_signed(uint16_t value)
{
    return (int32_t)value-((value&0x8000u)?65536:0);
}
#endif
