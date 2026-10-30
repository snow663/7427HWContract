#include "hardware.h"
#include "reference_math.h"
#define RUN(call) do { PcmStatus result = (call); if (result != PCM_OK) return result; } while (0)
/* 8548..858A. The caller must retain the stock IRQ-mask contract. */
PcmStatus pcm_fuel_async(Pcm *pcm, uint16_t pulse)
{
    if (pcm->calibration == NULL) return PCM_BAD_CONFIGURATION;
    const PcmReferenceCalibration *cal = &pcm->calibration->reference;
    if ((cal->mode_e & 0x10u) && pulse < 256) {
        uint8_t input = pulse < 32 ? 0 : (uint8_t)(pulse - 32);
        pulse = (uint16_t)(pulse + pcm_lookup16(input, cal->short_pulse));
        pulse = pulse < cal->short_subtract ? 0 : (uint16_t)(pulse - cal->short_subtract);
    }
    pulse = (uint16_t)(pulse + pcm->reference.additive_offset);
    RUN(pcm_write16(pcm, PCM_ASYNC_PACKET, pulse));
    uint16_t control;
    RUN(pcm_read16(pcm, PCM_BOARD_CONTROL, &control));
    control &= 0xfbffu;
    RUN(pcm_write16(pcm, PCM_BOARD_CONTROL, control));
    return pcm_write16(pcm, PCM_BOARD_CONTROL, (uint16_t)(control | 0x0400u));
}
