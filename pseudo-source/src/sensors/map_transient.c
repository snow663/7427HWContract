#include "board_io.h"
/* 7DB6..7DF0, before fuel TPS acquisition. Preserve nonzero A0
 * qualification and the extra admitted call after countdown expiry. */
PcmStatus pcm_map_transient(Pcm *pcm)
{
    if (pcm->calibration==NULL || pcm->calibration->io==NULL) return PCM_BAD_CONFIGURATION;
    const PcmIoCalibration *cal=pcm->calibration->io;
    uint8_t context=pcm->io.ac_mirror?0x10u:0u;
    if (!(pcm->calibration->mode_f&0x80u)) context+=(pcm->transmission.range_context&0x20u);
    uint8_t current=pcm->spark.rpm_high,previous=pcm->io.map_previous_rpm;
    uint8_t difference=current>=previous?(uint8_t)(current-previous):(uint8_t)(previous-current);
    bool changed=context!=(pcm->io.map_context&0xfeu) || difference>cal->map_rpm_delta_limit ||
                 !pcm->spark.idle_state || (pcm->io.coolant_context&0xa0u)==0;
    bool transient=true;
    if (changed) pcm->io.map_hold=cal->map_hold_reload;
    else if (pcm->io.map_hold) --pcm->io.map_hold;
    else transient=false;
    pcm->io.map_context=context;pcm->io.map_transient=transient;
    return PCM_OK;
}
