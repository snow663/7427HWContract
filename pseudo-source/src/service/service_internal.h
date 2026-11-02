#ifndef PCM_SERVICE_INTERNAL_H
#define PCM_SERVICE_INTERNAL_H
#include "service.h"
#include "serial.h"
#include "fuel.h"
#define SVC_RUN(call) do { PcmStatus svc_result=(call);if (svc_result!=PCM_OK) return svc_result; } while (0)
/* Foreign RMW retains read -> keep-mask sample -> write ordering. */
static inline PcmStatus svc_clear_bits(Pcm *pcm,uint16_t address,uint8_t mask)
{
    uint8_t value;SVC_RUN(pcm_serial_memory_read8(pcm,address,&value));
    return pcm_serial_memory_write8(pcm,address,(uint8_t)(value&~mask));
}
#endif
