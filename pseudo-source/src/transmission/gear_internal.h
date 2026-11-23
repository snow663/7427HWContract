#ifndef PCM_GEAR_INTERNAL_H
#define PCM_GEAR_INTERNAL_H

#include "control.h"
#include "../system/system_internal.h"

/* 0099 is also consumed as named state by C514 and the fuel cut gate. */
static inline PcmStatus gear_publish_fault_bit(Pcm *pcm, uint8_t mask, bool active)
{
    uint8_t flags;
    SYS_RUN(pcm_read8(pcm, 0x0099, &flags));
    flags = active ? (uint8_t)(flags | mask) : (uint8_t)(flags & (uint8_t)~mask);
    SYS_RUN(pcm_write8(pcm, 0x0099, flags));
    pcm->transmission.inhibit_flags = flags;
    return PCM_OK;
}

/* Direct per-gear arrays use ABX twice, preserving the ninth offset bit. */
static inline PcmStatus gear_column_pointer(Pcm *pcm, uint16_t field, uint8_t gear, uint16_t *pointer)
{
    uint16_t table;
    SYS_RUN(pcm_read16(pcm, field, &table));
    return pcm_read16(pcm, (uint16_t)(table + 2u * gear), pointer);
}

/* The table word precedes the selector byte at each Y-relative call site. */
static inline PcmStatus gear_select_field(Pcm *pcm, uint16_t field, uint16_t selector_address,
                                          uint8_t gear, uint16_t *address, bool *valid)
{
    uint16_t table;
    uint8_t selector;
    SYS_RUN(pcm_read16(pcm, field, &table));
    SYS_RUN(pcm_read8(pcm, selector_address, &selector));
    return pcm_transmission_descriptor(pcm, table, selector, gear, address, valid);
}

/* The two speed routines share this tail. The gain applies to the main
 * threshold. The floor receives its own cold correction afterwards. */
static inline PcmStatus gear_finish_threshold(Pcm *pcm, uint16_t gain_field, uint8_t main_value,
                                              uint8_t main_offset, uint8_t floor_value,
                                              uint8_t floor_offset, uint8_t *value, bool *valid)
{
    uint16_t main_word, floor_word, gain_table;
    SYS_RUN(pcm_transmission_cold_offset(pcm, (uint16_t)(main_value * 256u),
                                         (uint16_t)(main_offset * 256u), &main_word));
    SYS_RUN(pcm_read16(pcm, gain_field, &gain_table));
    SYS_RUN(pcm_transmission_temperature_gain(pcm, gain_table, main_word, &main_word));
    SYS_RUN(pcm_transmission_cold_offset(pcm, (uint16_t)(floor_value * 256u),
                                         (uint16_t)(floor_offset * 256u), &floor_word));
    *value = (uint8_t)((main_word >= floor_word ? main_word : floor_word) >> 8);
    *valid = true;
    return PCM_OK;
}
#endif
