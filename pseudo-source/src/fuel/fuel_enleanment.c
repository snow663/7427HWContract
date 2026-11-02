#include "fuel.h"
#include "delivery_internal.h"
#include "hardware.h"
/*824D..82EC. Rounded history bytes cap before subtracting current inputs. */
PcmStatus pcm_fuel_enleanment(Pcm *pcm)
{
    pcm->runtime.deceleration_fuel_cut=false;pcm->fuel.reduction_factor=255;
    uint8_t throttle=mix_byte(((uint32_t)pcm->fuel.throttle_decel_filter+128u)>>8);
    if (throttle<pcm->reference.throttle) goto inactive;
    pcm->fuel.throttle_drop=(uint8_t)(throttle-pcm->reference.throttle);
    DL_CAL();
    if (!((pcm->calibration->reference.mode_b & 0x80u) && pcm->fuel.decel_throttle_latch)) {
        if (pcm->fuel.throttle_drop<=cal->throttle_drop_minimum) goto inactive;
        pcm->fuel.decel_throttle_latch=true;
    }
    uint8_t load=mix_byte(((uint32_t)pcm->fuel.map_history+128u)>>8);
    if (load<pcm->spark.load_coordinate) goto inactive;
    load=(uint8_t)(load-pcm->spark.load_coordinate);
    if (load<=cal->load_drop_minimum) goto inactive;
    uint8_t gain=mix_byte((unsigned)pcm_lookup16(mix_min(load,160),cal->enleanment_load)+pcm_lookup16(pcm->fuel.throttle_drop,cal->enleanment_throttle));
    gain=mix_byte(((uint32_t)gain*pcm->fuel.base_ae_gain)>>5);
    if (pcm->spark.vehicle_speed_high<cal->enleanment_speed) gain=mix_double_round(gain,cal->slow_enleanment_gain);
    gain=(uint8_t)(0u-gain);
    if (gain==0) goto inactive;
    pcm->fuel.decel_enleanment=true;
    pcm->fuel.acceleration_reservoir=pcm_gain_word(pcm->fuel.acceleration_reservoir,gain);
    return pcm_fuel_pulse_scale(pcm,gain);
inactive:
    pcm->fuel.decel_enleanment=false;pcm->fuel.decel_throttle_latch=false;return PCM_OK;
}
