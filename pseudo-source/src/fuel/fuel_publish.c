#include "fuel.h"
#include "hardware.h"
#include "reference_math.h"
/* 84F5..852B. Callable crank entry bypasses short-PW shaping. Tail852C is
 * separate scheduled work. Offset addition wraps BEFORE the7FFF comparison. */
PcmStatus pcm_fuel_publish(Pcm *pcm, uint16_t pulse)
{
    pcm->reference.delivered_pulse = pulse;
    if (pulse != 0) {
        pulse = (uint16_t)(pulse + pcm->reference.additive_offset);
        if (pulse >= 0x7fffu) pulse = 0x7fff;
    }
    pcm->reference.timer_pulse = pulse;
    if (pcm->calibration == NULL) return PCM_BAD_CONFIGURATION;
    if (!(pcm->calibration->reference.mode_b & 1u)) return pcm_write16(pcm, PCM_INJECTOR_WORD, pulse);
    if (pcm->calibration->fuel == NULL) return PCM_BAD_CONFIGURATION;
    uint32_t delay = (uint32_t)pcm_gain_word(pcm->spark.period_basis, pcm->calibration->fuel->injection_delay_gain) * 4u;
    pcm->reference.timer_delay = delay > 65535u ? 65535u : (uint16_t)delay;
    return PCM_OK;
}
