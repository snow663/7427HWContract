#ifndef PSEUDO_SOURCE_REFERENCE_MATH_H
#define PSEUDO_SOURCE_REFERENCE_MATH_H
#include "pcm.h"
uint8_t pcm_lookup16(uint8_t input, const uint8_t knots[17]);
uint16_t pcm_gain_word(uint16_t word, uint8_t gain);
uint16_t pcm_crank_event_gain(const Pcm *);
#endif
