#include "gear_internal.h"

/* D8A7..D8CD. When D8FE sets carry, its returned X is the RPM base.
 * A stop retains the table cursor while a selected null pointer returns zero. */
PcmStatus pcm_transmission_kickdown_rpm(Pcm *pcm, uint16_t group, uint8_t gear, uint16_t *value)
{
    if (pcm == NULL || value == NULL) return PCM_BAD_CONFIGURATION;
    uint16_t pointer, offset = 0, base, corrected, table;
    bool found;
    SYS_RUN(gear_column_pointer(pcm, (uint16_t)(group + 2u), gear, &pointer));
    if (pointer != 0) SYS_RUN(pcm_read16(pcm, pointer, &offset));
    SYS_RUN(gear_select_field(pcm, group, 0x0081, gear, &base, &found));
    if (found) SYS_RUN(pcm_read16(pcm, base, &base));
    SYS_RUN(pcm_transmission_cold_offset(pcm, base, offset, &corrected));
    SYS_RUN(pcm_read16(pcm, (uint16_t)(group + 4u), &table));
    return pcm_transmission_temperature_gain(pcm, table, corrected, value);
}
