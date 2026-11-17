#ifndef PCM_SYSTEM_INTERNAL_H
#define PCM_SYSTEM_INTERNAL_H
#include "system.h"
#include "serial.h"
#include "hardware.h"
#define SYS_RUN(call) do { PcmStatus sys_status=(call);if (sys_status!=PCM_OK) return sys_status; } while (0)
/* Logical RAM must be bound to its canonical named owners by the provider. */
static inline PcmStatus sys_update(Pcm *pcm,uint16_t address,uint8_t clear,uint8_t set)
{
    uint8_t value;SYS_RUN(pcm_serial_memory_read8(pcm,address,&value));
    return pcm_serial_memory_write8(pcm,address,(uint8_t)((value&~clear)|set));
}
/* F436: the coefficient is sampled two or three times. Keep those reads
 * distinct even when the provider normally supplies immutable calibration. */
static inline PcmStatus sys_lag16(Pcm *pcm,uint16_t target,uint16_t old,
                                 uint16_t coefficient,uint16_t *out)
{
    uint16_t difference=(uint16_t)(target-old);uint8_t gain;
    SYS_RUN(pcm_read8(pcm,coefficient,&gain));
    uint16_t partial=(uint16_t)(old+(difference>>8)*gain);
    if (target<old) {
        SYS_RUN(pcm_read8(pcm,coefficient,&gain));
        partial=(uint16_t)(partial-(uint16_t)gain*256u);
    }
    SYS_RUN(pcm_read8(pcm,coefficient,&gain));
    *out=(uint16_t)(partial+(((difference&255u)*gain+128u)>>8));
    return PCM_OK;
}
/* F4C1: capture the adjacent knots as one word, then reread the base knot
 * after interpolation. The helper's private stack is outside this interface. */
static inline PcmStatus sys_curve16(Pcm *pcm,uint8_t input,uint16_t table,uint8_t *out)
{
    uint16_t address=(uint16_t)(table+(input>>4)),knots;uint8_t base;
    SYS_RUN(pcm_read16(pcm,address,&knots));
    uint8_t first=(uint8_t)(knots>>8),second=(uint8_t)knots;
    uint8_t difference=first>second?(uint8_t)(first-second):(uint8_t)(second-first);
    uint8_t step=(uint8_t)(((uint16_t)difference*(uint8_t)(input<<4)+128u)>>8);
    SYS_RUN(pcm_read8(pcm,address,&base));
    *out=first>=second?(uint8_t)(base-step):(uint8_t)(base+step);
    return PCM_OK;
}
#endif
