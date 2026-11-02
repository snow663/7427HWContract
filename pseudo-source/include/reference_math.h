#ifndef PSEUDO_SOURCE_REFERENCE_MATH_H
#define PSEUDO_SOURCE_REFERENCE_MATH_H
#include "pcm.h"
/* Caller supplies at least (input>>4)+2 knots. Bounded-input tables may be shorter. */
uint8_t pcm_lookup16(uint8_t input, const uint8_t *knots);
uint16_t pcm_gain_word(uint16_t word, uint8_t gain);
uint16_t pcm_crank_event_gain(const Pcm *);
PcmStatus pcm_lookup2d(uint8_t row, uint8_t column, const PcmTable2D *, uint8_t *result);
uint16_t pcm_lag8(uint8_t target, uint16_t old, uint8_t gain);
/* F436 returns the result; F479 also exposes the intermediate destination store. */
uint16_t pcm_lag16(uint16_t target, uint16_t old, uint8_t gain, uint16_t *intermediate);
PcmStatus pcm_lookup_capped(uint8_t input, const PcmCappedCurve *, uint8_t *result);
PcmStatus pcm_lookup_scaled(uint8_t input, const PcmScaledCurve *, uint8_t *result);
PcmStatus pcm_lookup_offset(uint8_t input, const PcmOffsetCurve *, uint8_t *result);
#endif
