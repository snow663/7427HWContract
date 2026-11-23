#include "gear_internal.h"

/* D7E5..D83F. Interpolate the speed and cold curves at B2. Their
 * independently sampled first knots supply the cold-corrected floor. */
PcmStatus pcm_transmission_normal_threshold(Pcm *pcm, uint16_t group, uint8_t gear,
                                            uint8_t *value, bool *valid)
{
    if (pcm == NULL || value == NULL || valid == NULL) return PCM_BAD_CONFIGURATION;
    uint8_t throttle, first, speed, main_offset = 0, floor_offset = 0;
    uint16_t pointer;
    SYS_RUN(gear_column_pointer(pcm, (uint16_t)(group + 8u), gear, &pointer));
    if (pointer != 0) {
        uint8_t cold;
        SYS_RUN(pcm_read8(pcm, 0x00b2, &throttle));
        SYS_RUN(sys_curve16(pcm, throttle, pointer, &cold));
        SYS_RUN(pcm_read8(pcm, pointer, &first));
        main_offset = (uint8_t)(cold - 128u);
        floor_offset = (uint8_t)(first - 128u);
    }
    bool found;
    SYS_RUN(gear_select_field(pcm, (uint16_t)(group + 6u), 0x0080, gear, &pointer, &found));
    if (!found) {
        *value = 0;
        *valid = false;
        return PCM_OK;
    }
    SYS_RUN(pcm_read8(pcm, 0x00b2, &throttle));
    SYS_RUN(sys_curve16(pcm, throttle, pointer, &speed));
    SYS_RUN(pcm_read8(pcm, pointer, &first));
    return gear_finish_threshold(pcm, (uint16_t)(group + 10u), speed, main_offset,
                                 first, floor_offset, value, valid);
}
