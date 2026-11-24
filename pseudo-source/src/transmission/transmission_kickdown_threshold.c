#include "gear_internal.h"

static PcmStatus cold_scalar(Pcm *pcm, uint16_t field, uint8_t gear, uint8_t *offset)
{
    uint16_t pointer;
    SYS_RUN(gear_column_pointer(pcm, field, gear, &pointer));
    uint8_t scalar = 128;
    if (pointer != 0) SYS_RUN(pcm_read8(pcm, pointer, &scalar));
    *offset = (uint8_t)(scalar - 128u);
    return PCM_OK;
}

/* D840..D8A6. The normal descriptor supplies a floor when present.
 * The kickdown descriptor supplies the main scalar and determines validity. */
PcmStatus pcm_transmission_kickdown_threshold(Pcm *pcm, uint16_t group, uint8_t gear,
                                              uint8_t *value, bool *valid)
{
    if (pcm == NULL || value == NULL || valid == NULL) return PCM_BAD_CONFIGURATION;
    uint8_t speed, floor = 0, main_offset, floor_offset;
    uint16_t pointer;
    bool found;
    SYS_RUN(cold_scalar(pcm, (uint16_t)(group + 2u), gear, &main_offset));
    SYS_RUN(cold_scalar(pcm, (uint16_t)(group + 8u), gear, &floor_offset));
    SYS_RUN(gear_select_field(pcm, (uint16_t)(group + 6u), 0x0080, gear, &pointer, &found));
    if (found) SYS_RUN(pcm_read8(pcm, pointer, &floor));
    SYS_RUN(gear_select_field(pcm, group, 0x0081, gear, &pointer, &found));
    if (!found) {
        *value = 0;
        *valid = false;
        return PCM_OK;
    }
    SYS_RUN(pcm_read8(pcm, pointer, &speed));
    return gear_finish_threshold(pcm, (uint16_t)(group + 4u), speed, main_offset,
                                 floor, floor_offset, value, valid);
}
