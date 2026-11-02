#include "board_io.h"
/* 7D21..7D4A. Agreement clears the counter. An old count>=limit publishes
 * the inverse input; incrementing to the limit does not publish early. */
PcmStatus pcm_brake_filter(Pcm *pcm)
{
    if (pcm->io.brake_active!=((pcm->iac.input_shadow&2u)!=0)) {
        pcm->io.brake_count=0;return PCM_OK;
    }
    if (pcm->calibration==NULL || pcm->calibration->io==NULL) return PCM_BAD_CONFIGURATION;
    if (pcm->io.brake_count<pcm->calibration->io->brake_delay) ++pcm->io.brake_count;
    else {
        pcm->io.brake_active=false;
        if (!(pcm->iac.input_shadow&2u)) pcm->io.brake_active=true;
    }
    return PCM_OK;
}
