#include "fuel.h"
#include "board_io.h"
/* 7DF1..7E08. Save the prior engine TPS before normalizing the shared raw input. */
PcmStatus pcm_fuel_throttle(Pcm *pcm)
{
    pcm->spark.previous_throttle = pcm->reference.throttle;
    uint8_t value;
    PcmStatus result = pcm_throttle_normalize(pcm, &value);
    if (result != PCM_OK) return result;
    pcm->reference.throttle = pcm->fuel.throttle_fault ? pcm->calibration->air->throttle_default : value;
    return PCM_OK;
}
