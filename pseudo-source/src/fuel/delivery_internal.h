#ifndef PCM_DELIVERY_INTERNAL_H
#define PCM_DELIVERY_INTERNAL_H
#include "mixture_internal.h"
#define DL_CAL() \
    if (pcm->calibration==NULL || pcm->calibration->delivery==NULL) return PCM_BAD_CONFIGURATION; \
    const PcmDeliveryCalibration *cal=pcm->calibration->delivery
#define DL_RUN(call) MIX_RUN(call)
static inline uint16_t dl_accumulator(const Pcm *pcm)
{ return (uint16_t)((uint16_t)pcm->fuel.async_accumulator_high*256u+(pcm->fuel.async_accumulator_fraction>>8)); }
static inline void dl_store_accumulator(Pcm *pcm,uint16_t word)
{
    pcm->fuel.async_accumulator_high=(uint8_t)(word>>8);
    pcm->fuel.async_accumulator_fraction=(uint16_t)((word<<8)|(pcm->fuel.async_accumulator_fraction&255u));
}
#endif
