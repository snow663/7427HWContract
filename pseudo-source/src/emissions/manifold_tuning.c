#include "control.h"
#include "hardware.h"
#include "../system/system_internal.h"

/* D472..D4A2. The entry row is one byte after the retained row. */
PcmStatus pcm_manifold_tuning(Pcm *pcm)
{
    if (pcm == NULL || pcm->calibration == NULL) return PCM_BAD_CONFIGURATION;
    uint8_t flags, limit;
    if (pcm->calibration->reference.mode_e & 8u) {
        uint16_t row = 0x412b;
        SYS_RUN(pcm_read8(pcm, 0x52, &flags));
        if (!(flags & 8u)) {
            uint8_t temperature = pcm->io.coolant_conversion;
            SYS_RUN(pcm_read8(pcm, 0x4131, &limit));
            if (temperature < limit) goto clear;
            ++row;
        }
        uint8_t rpm = pcm->reference.rpm_coordinate;
        SYS_RUN(pcm_read8(pcm, row, &limit));
        if (rpm <= limit) goto clear;
        SYS_RUN(pcm_read8(pcm, (uint16_t)(row + 2u), &limit));
        if (rpm > limit) goto clear;
        uint8_t throttle = pcm->reference.throttle;
        SYS_RUN(pcm_read8(pcm, (uint16_t)(row + 4u), &limit));
        if (throttle > limit) return pcm_update8(pcm, 0x52, 0, 8);
    }
clear:
    return pcm_update8(pcm, 0x52, 8, 0);
}
