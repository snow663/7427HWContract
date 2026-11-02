#include "fuel.h"
#include "delivery_internal.h"
#include "hardware.h"
/*821D..823A. Earlier branches can enter directly, bypassing the decel gate. */
PcmStatus pcm_fuel_reduction(Pcm *pcm)
{
    pcm->runtime.deceleration_fuel_cut=true;
    DL_CAL();
    pcm->fuel.decel_timer=cal->decel_active_reload;pcm->fuel.decel_enleanment=true;
    pcm->fuel.reduction_factor=mix_sub(pcm->fuel.reduction_factor,cal->reduction_step);
    return pcm_fuel_pulse_scale(pcm,pcm->fuel.reduction_factor);
}
