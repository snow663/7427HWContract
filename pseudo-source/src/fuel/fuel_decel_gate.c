#include "fuel.h"
#include "delivery_internal.h"
#include "hardware.h"
/*8175..824C. true selects reduction821D; false selects enleanment824D. */
PcmStatus pcm_fuel_decel_gate(Pcm *pcm, bool *reduce)
{
    if (reduce == NULL) return PCM_BAD_CONFIGURATION;
    *reduce=false;DL_CAL();
    if (pcm->reference.coolant < cal->decel_coolant) return PCM_OK;
    if (pcm->iac.park_neutral) goto recovery;
    if (!(pcm->spark.load_status & 0x24u)) {
        uint8_t threshold;DL_RUN(mix_h1(pcm->reference.rpm_coordinate,32,&cal->decel_throttle,&threshold));
        if (threshold<=pcm->reference.throttle) {
            if (pcm->runtime.deceleration_fuel_cut) pcm->io.coolant_context |= 1u;
            goto reset;
        }
    }
    if (pcm->io.map_previous_rpm>pcm->spark.rpm_high && pcm->io.map_previous_rpm-pcm->spark.rpm_high>cal->decel_rpm_change) goto recovery;
    if (!(pcm->spark.load_status & 0x48u)) {
        if (pcm->fuel.map_delta>cal->decel_map_change) goto recovery;
        uint8_t load=(pcm->calibration->reference.mode_e & 2u) ? pcm->spark.normalized_load : pcm->spark.load_coordinate;
        if (load>=cal->decel_load_entry && (!pcm->runtime.deceleration_fuel_cut || load>=cal->decel_load_retained)) goto reload;
    }
    uint8_t rpm=pcm->io.environmental_factor;
    if (!pcm->runtime.deceleration_fuel_cut) rpm=mix_byte((unsigned)rpm+cal->decel_rpm_adder);
    if (pcm->reference.rpm_coordinate<=rpm) goto recovery;
    if (!(pcm->runtime.primary_faults & 0x10u) && pcm->spark.vehicle_speed_high < cal->decel_speed[pcm->runtime.deceleration_fuel_cut ? 1 : 0]) goto recovery;
    if (pcm->fuel.decel_delay==0) { *reduce=true;return PCM_OK; }
    if (!(pcm->scheduler.phase & 0x0eu)) --pcm->fuel.decel_delay;
    goto age;
recovery:
    if (pcm->fuel.decel_timer!=0) {
        uint32_t sum=(uint32_t)pcm->fuel.acceleration_reservoir+cal->recovery_fuel;
        pcm->fuel.acceleration_reservoir=sum>65535u ? 32767 : (uint16_t)sum;
        pcm->fuel.async_pending=true;
    }
reset:
    pcm->fuel.decel_timer=0;
reload:
    pcm->fuel.decel_delay=cal->decel_delay;
age:
    if (pcm->fuel.decel_timer!=0) --pcm->fuel.decel_timer;
    return PCM_OK;
}
