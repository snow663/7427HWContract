#include "iac.h"
#include "reference_math.h"
/* 9EA3..9EE9. Strict speed comparison and byte DEC expiry, with distinct
 * DFCO borrow/equality behavior. The stock speed limitFF disables that gate. */
PcmStatus pcm_iac_movement(Pcm *pcm)
{
    if (pcm->calibration == NULL || pcm->calibration->iac == NULL) return PCM_BAD_CONFIGURATION;
    const PcmIacCalibration *cal = pcm->calibration->iac;
    if (!(pcm->iac.state_flags & 2u) && pcm->spark.vehicle_speed_high > cal->movement_speed_limit) {
        pcm->iac.bank[0].cold = pcm_gain_word(pcm->iac.bank[0].cold, cal->movement_gain);
        pcm->iac.bank[1].cold = pcm_gain_word(pcm->iac.bank[1].cold, cal->movement_gain);
        pcm->iac.state_flags |= 2u;
    }
    uint8_t amount = pcm->iac.dfco_adder;
    if (amount != 0 && !pcm->runtime.deceleration_fuel_cut) {
        if (--pcm->iac.dfco_divider == 0) {
            pcm->iac.dfco_divider = cal->dfco_decay_reload;
            if (amount < cal->dfco_decay_amount) { amount = 0;pcm->iac.transfer_flags &= (uint8_t)~0x20u; }
            else amount = (uint8_t)(amount - cal->dfco_decay_amount);
            pcm->iac.dfco_adder = amount;
        }
    }
    return PCM_OK;
}
