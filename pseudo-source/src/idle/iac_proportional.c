#include "iac.h"
#include "iac_math.h"
#include "reference_math.h"
/* 9C20..9C95. Source views follow the eight verified9C96 pointer words. */
PcmStatus pcm_iac_proportional(Pcm *pcm)
{
    if (pcm->calibration == NULL || pcm->calibration->iac == NULL) return PCM_BAD_CONFIGURATION;
    const PcmIacCalibration *cal = pcm->calibration->iac;
    bool high = (pcm->iac.context & 0x80u) != 0;
    unsigned curve = high ? 1 : 0;
    uint8_t error = pcm->iac.rpm_error;
    if (pcm->iac.context & 2u) {
        curve = 2u + 4u * (pcm->iac.context & 1u) + 2u * ((pcm->iac.context & 8u) != 0) + high;
        if (high) {
            uint8_t speed = pcm->spark.vehicle_speed_high;
            if (speed >= cal->proportional_speed_entry) pcm->iac.kicker_flags |= 0x40u;
            else if (speed < cal->proportional_speed_exit) pcm->iac.kicker_flags &= (uint8_t)~0x40u;
            if ((pcm->iac.kicker_flags & 0x40u) && error >= cal->proportional_error_limit) error = cal->proportional_error_limit;
        }
    }
    pcm->iac.proportional = pcm_lookup16(iac_error_coordinate(error), cal->proportional_curve[curve]);
    return PCM_OK;
}
