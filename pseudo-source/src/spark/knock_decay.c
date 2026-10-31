#include "knock.h"
#include "reference_math.h"
/* CEBB..CEDA. Phase bit4 gates decay, not the following sensor diagnostic. */
PcmStatus pcm_knock_decay(Pcm *pcm)
{
    if (pcm->calibration == NULL) return PCM_BAD_CONFIGURATION;
    if (pcm->scheduler.phase & 0x10u) return PCM_OK;
    uint8_t rate = pcm_lookup16(pcm->reference.rpm_coordinate, pcm->calibration->knock.decay_rate);
    uint8_t step = (uint8_t)(((uint16_t)rate * pcm->knock.retard + 128u) >> 8);
    if (step == 0) step = 1;
    uint8_t old = pcm->knock.retard; /* CED2 reads it again after MUL/rounding. */
    pcm->knock.retard = old >= step ? (uint8_t)(old - step) : 0;
    return PCM_OK;
}
