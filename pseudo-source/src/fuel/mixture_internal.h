#ifndef PCM_MIXTURE_INTERNAL_H
#define PCM_MIXTURE_INTERNAL_H
#include "reference_math.h"
#define MIX_CAL() \
    if (pcm->calibration == NULL || pcm->calibration->mixture == NULL) return PCM_BAD_CONFIGURATION; \
    const PcmMixtureCalibration *cal = pcm->calibration->mixture
#define MIX_RUN(call) do { PcmStatus mix_result = (call); if (mix_result != PCM_OK) return mix_result; } while (0)
static inline uint8_t mix_min(uint8_t a, uint8_t b) { return a < b ? a : b; }
static inline uint8_t mix_sub(uint8_t a, uint8_t b) { return a > b ? (uint8_t)(a-b) : 0; }
static inline uint8_t mix_byte(unsigned v) { return v > 255u ? 255 : (uint8_t)v; }
static inline uint16_t mix_word(uint32_t v) { return v > 65535u ? 65535 : (uint16_t)v; }
static inline uint8_t mix_round(uint8_t a, uint8_t b) { return (uint8_t)(((uint16_t)a*b+128u)>>8); }
static inline uint8_t mix_double(uint8_t a, uint8_t b) { return mix_byte(((uint32_t)a*b)>>7); }
static inline uint8_t mix_double_round(uint8_t a, uint8_t b) { return mix_byte(((uint32_t)a*b+64u)>>7); }
static inline uint16_t mix_fraction(uint16_t n, uint16_t d) { return d == 0 || n >= d ? 65535 : (uint16_t)(((uint32_t)n<<16)/d); }
/* F49A: cap before subtracting the caller's offset, then F4C1 interpolation. */
static inline PcmStatus mix_h1(uint8_t input, uint8_t offset, const PcmCappedCurve *curve, uint8_t *out)
{
    if (curve == NULL || curve->values == NULL) return PCM_BAD_CONFIGURATION;
    input = mix_sub(mix_min(input, curve->limit), offset);
    if ((input>>4)+1u >= curve->length) return PCM_BAD_CONFIGURATION;
    *out = pcm_lookup16(input, curve->values);
    return PCM_OK;
}
#endif
