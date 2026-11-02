#include "fuel.h"
#include "feedback_internal.h"
#include "hardware.h"
static bool retain(uint8_t value, uint8_t bin, const uint8_t *bounds, uint8_t margin)
{
    if (bin != 0 && bounds[bin-1u] >= margin && value < bounds[bin-1u]-margin) return false;
    if (bin != 3 && (unsigned)bounds[bin]+margin <= 255u && value > (unsigned)bounds[bin]+margin) return false;
    return true;
}
static uint8_t bin(uint8_t value, const uint8_t *bounds)
{
    uint8_t index=0;
    while (index<3 && value>=bounds[index]) ++index;
    return index;
}
/*8C73..8D9D. Phase9F samples the speed magnitude consumed by the earlier PE. */
PcmStatus pcm_blm_select(Pcm *pcm)
{
    if (pcm->scheduler.phase == 0x9fu) {
        uint16_t speed = (uint16_t)((uint16_t)pcm->spark.vehicle_speed_high*256u+pcm->io.vehicle_speed_fraction);
        uint16_t old = pcm->fuel.previous_vehicle_speed;
        pcm->fuel.pe_vehicle_change = speed >= old ? (uint16_t)(speed-old) : (uint16_t)(old-speed);
        pcm->fuel.previous_vehicle_speed = speed;
    }
    pcm->fuel.blm_transition = false;
    FB_CAL();
    uint8_t index, old = pcm->iac.blm_cell_index;
    bool changed;
    if ((cal->special_cells & 1u) && pcm->reference.throttle < cal->idle_throttle && pcm->spark.vehicle_speed_high < cal->idle_speed) {
        index = 16;
        if ((cal->special_cells & 2u) && pcm->io.ac_mirror) ++index;
        if ((cal->special_cells & 4u) && pcm->iac.park_neutral) index+=2;
        if (pcm->reference.packet_updated) index = 20;
        changed = index != old;
    } else {
        uint8_t load = (pcm->calibration->reference.mode_e & 1u) ? pcm->spark.normalized_load : pcm->spark.load_coordinate;
        changed = old>=16 || !retain(pcm->reference.rpm_coordinate,old&3u,cal->rpm_bins,cal->rpm_margin) ||
            !retain(load,(old>>2)&3u,cal->load_bins,cal->load_margin);
        index = changed ? (uint8_t)(bin(pcm->reference.rpm_coordinate,cal->rpm_bins)+4u*bin(load,cal->load_bins)) : old;
    }
    if (changed) {
        pcm->fuel.blm_transition = true;pcm->fuel.blm_cell_changed = true;pcm->fuel.asynchronous_active = true;
    }
    uint8_t value = pcm->fuel.blm_cells[index];
    if (value > cal->blm_maximum || value < cal->blm_minimum[index<16 ? 0 : 1]) {
        pcm->fuel.blm_invalid = true;
        FB_RUN(pcm_blm_reset(pcm));value = 128;
    }
    pcm->iac.blm_value = value;pcm->iac.blm_cell_index = index;
    return PCM_OK;
}
