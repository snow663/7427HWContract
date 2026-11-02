#include "fuel.h"
#include "delivery_internal.h"
#include "hardware.h"
/*842C..8468. Caller supplies the zero-write/11-cycle-gap prefix. */
PcmStatus pcm_fuel_async_accumulate(Pcm *pcm)
{
    uint16_t period;DL_RUN(pcm_read16(pcm,PCM_REFERENCE_PERIOD,&period));
    uint16_t ratio=mix_fraction(pcm->fuel.corrected_pulse,mix_word(2u*period));
    uint16_t integer=(uint16_t)(ratio/80u), remainder=(uint16_t)(ratio%80u);
    uint32_t fraction=((uint32_t)remainder<<16)/80u+128u;
    pcm->fuel.async_remainder=(uint8_t)(fraction>>8);
    if (fraction>65535u) ++integer;
    pcm->fuel.async_quotient=integer;
    uint16_t increment=(uint16_t)((integer<<8)|pcm->fuel.async_remainder);
    uint32_t low=(uint32_t)pcm->fuel.async_accumulator_fraction+increment;
    pcm->fuel.async_accumulator_fraction=(uint16_t)low;
    pcm->fuel.async_accumulator_high=(uint8_t)(pcm->fuel.async_accumulator_high+(integer>>8)+(low>>16));
    return PCM_OK;
}
