#ifndef PCM_SLOT4_MONITOR_H
#define PCM_SLOT4_MONITOR_H
#include "diagnostic_internal.h"

/* Publish the live diagnostic bit only after the addressed write succeeds.
 * Other bits in a named owner may have been updated by a different controller. */
static inline PcmStatus slot4_fault_bit(Pcm *pcm, uint16_t address, uint8_t bit, bool set)
{
    SYS_RUN(pcm_update8(pcm, address, bit, set ? bit : 0));
    volatile uint8_t *owner = NULL;
    if (address == 0x16) owner = &pcm->runtime.primary_faults;
    if (address == 0x1d) owner = &pcm->transmission.fault_flags_secondary;
    if (owner != NULL) *owner = (uint8_t)((*owner & (uint8_t)~bit) | (set ? bit : 0));
    return PCM_OK;
}

/* Codes 14/15, 58/59, 63/64 and 75 qualify entry and recovery alike.
 * Compare the incremented wrapping timer. A matched state resets the timer. */
static inline PcmStatus slot4_debounce(Pcm *pcm, uint16_t status, uint8_t bit, bool fault,
                                       uint16_t counter, uint8_t age, uint16_t delay)
{
    uint8_t live, limit;
    DG8(status, live);
    if (((live & bit) != 0) != fault) {
        age = (uint8_t)(age + 1u);
        DG8(delay, limit);
        if (age < limit) return pcm_write8(pcm, counter, age);
        SYS_RUN(slot4_fault_bit(pcm, status, bit, fault));
    }
    return pcm_write8(pcm, counter, 0);
}

static inline PcmStatus slot4_input_monitor(Pcm *pcm, uint16_t enable, uint16_t status, uint8_t bit,
                                           uint16_t counter, const volatile uint8_t *sample,
                                           uint16_t threshold, bool below)
{
    if (pcm->runtime.monitor_freeze) return PCM_OK;
    uint8_t flags, age, limit;
    DG8(enable, flags);
    if (!(flags & bit)) return pcm_write8(pcm, counter, 0);
    DG8(counter, age);
    uint8_t value = *sample;
    DG8(threshold, limit);
    return slot4_debounce(pcm, status, bit, below ? value < limit : value > limit,
                          counter, age, (uint16_t)(threshold + 1u));
}

/* A good observation consumes its latch even when the live fault is clear
 * or the retained recovery budget rejects clearing it. Battery monitors
 * omit the budget; the three solenoid monitors add two with byte wrap. */
static inline PcmStatus slot4_recover_once(Pcm *pcm, uint16_t observed, uint8_t seen,
                                           uint16_t status, uint8_t bit,
                                           uint16_t budget, uint16_t ceiling)
{
    uint8_t flags, used, limit;
    DG8(observed, flags);
    if (flags & seen) return PCM_OK;
    DG_SET(observed, seen);
    DG8(status, flags);
    if (!(flags & bit)) return PCM_OK;
    if (budget != 0) {
        DG8(budget, used);
        DG8(ceiling, limit);
        if (used >= limit) return PCM_OK;
        SYS_RUN(pcm_write8(pcm, budget, (uint8_t)(used + 2u)));
    }
    return slot4_fault_bit(pcm, status, bit, false);
}

/* ED3F/ED80/EDC1 read 009E again after qualifying bit 0. The code 83
 * BRSET checks both bits; 81 and 82 use BRCLR on individual bits. */
static inline PcmStatus slot4_solenoid_monitor(Pcm *pcm, uint8_t bit, uint8_t pattern,
                                               uint8_t observed_bit, uint16_t counter,
                                               uint16_t delay, uint16_t budget)
{
    if (pcm == NULL) return PCM_BAD_CONFIGURATION;
    if (pcm->runtime.monitor_freeze) return PCM_OK;
    uint8_t flags, age, limit;
    DG8(0x5b07, flags);
    if (!(flags & bit)) return pcm_write8(pcm, counter, 0);
    DG8(counter, age);
    DG8(0x9e, flags);
    bool fault = false;
    if (flags & 1u) {
        DG8(0x9e, flags);
        fault = pattern == 0x30u ? (flags & pattern) == pattern : (flags & pattern) == 0;
    }
    if (!fault) {
        SYS_RUN(slot4_recover_once(pcm, 0x96, observed_bit, 0x1d, bit, budget, (uint16_t)(delay + 1u)));
        return pcm_write8(pcm, counter, 0);
    }
    DG8(0x1d, flags);
    if (!(flags & bit)) {
        age = (uint8_t)(age + 1u);
        DG8(delay, limit);
        if (age < limit) return pcm_write8(pcm, counter, age);
        SYS_RUN(slot4_fault_bit(pcm, 0x1d, bit, true));
    }
    return pcm_write8(pcm, counter, 0);
}

static inline PcmStatus slot4_read_timer(Pcm *pcm, uint16_t address, bool word_timer, uint16_t *value)
{
    if (word_timer) return pcm_read16(pcm, address, value);
    uint8_t byte;
    SYS_RUN(pcm_read8(pcm, address, &byte));
    *value = byte;
    return PCM_OK;
}

static inline PcmStatus slot4_write_timer(Pcm *pcm, uint16_t address, bool word_timer, uint16_t value)
{
    if (word_timer) return pcm_write16(pcm, address, value);
    return pcm_write8(pcm, address, (uint8_t)value);
}

/* Both battery monitors use BHI for fault entry. The timer at 0169 and
 * its threshold are words. Code 53 uses a byte for both. */
static inline PcmStatus slot4_battery_monitor(Pcm *pcm, bool word_timer)
{
    if (pcm == NULL) return PCM_BAD_CONFIGURATION;
    if (pcm->runtime.monitor_freeze) return PCM_OK;
    const uint16_t counter = word_timer ? 0x169 : 0x16b;
    const uint16_t threshold = word_timer ? 0x5b63 : 0x5b66;
    const uint8_t bit = word_timer ? 0x10 : 0x08;
    uint8_t flags, limit;
    uint16_t age, timeout;
    DG8(0x5b04, flags);
    if (!(flags & bit)) return slot4_write_timer(pcm, counter, word_timer, 0);
    SYS_RUN(slot4_read_timer(pcm, counter, word_timer, &age));
    uint8_t sample = pcm->spark.battery_sample;
    DG8(threshold, limit);
    if (sample <= limit) {
        SYS_RUN(slot4_recover_once(pcm, word_timer ? 0x97 : 0x95, word_timer ? 1u : 2u,
                                   0x1a, bit, 0, 0));
    } else {
        DG8(0x1a, flags);
        if (!(flags & bit)) {
            age = word_timer ? (uint16_t)(age + 1u) : (uint8_t)(age + 1u);
            SYS_RUN(slot4_read_timer(pcm, (uint16_t)(threshold + 1u), word_timer, &timeout));
            if (age < timeout) return slot4_write_timer(pcm, counter, word_timer, age);
            DG_SET(0x1a, bit);
        }
    }
    return slot4_write_timer(pcm, counter, word_timer, 0);
}
#endif
