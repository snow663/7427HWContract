#include "iac.h"
#include "reference_math.h"
static uint16_t four(uint16_t value)
{ return value > 16383u ? UINT16_MAX : (uint16_t)(4u * value); }
/* 9CFD..9E98. Keep the filtered word local until9DEE; the minimum insertion
 * edits the saved frame. RPM overflow skips the later coolant multiplier. */
PcmStatus pcm_iac_follower(Pcm *pcm)
{
    if (pcm->calibration == NULL || pcm->calibration->iac == NULL) return PCM_BAD_CONFIGURATION;
    const PcmIacCalibration *cal = pcm->calibration->iac;
    uint8_t tps = pcm->reference.throttle;
    uint8_t requested = tps > 63u ? 255u : (uint8_t)(4u * tps);
    uint16_t filtered;
    if (requested > (pcm->iac.follower_filtered >> 8)) {
        unsigned drive = (pcm->iac.context & 2u) != 0;
        if (drive) {
            uint8_t speed = pcm->spark.vehicle_speed_high;
            if (speed > 80u) speed = 80;
            pcm->iac.follower_hold = pcm_lookup16((uint8_t)(2u * speed), cal->follower_drive_hold);
        }
        uint8_t cap = cal->follower_cap[drive];
        if (requested > cap) requested = cap;
        filtered = (uint16_t)((uint16_t)requested << 8);
    } else if (pcm->iac.follower_hold != 0) filtered = pcm->iac.follower_filtered;
    else {
        uint8_t gain = cal->follower_park_gain;
        if (pcm->iac.context & 2u) {
            uint8_t speed = pcm->spark.vehicle_speed_high;
            if (speed > 80u) speed = 80;
            gain = pcm_lookup16((uint8_t)(2u * speed), cal->follower_drive_gain);
        }
        if (pcm->spark.load_coordinate < cal->follower_load_limit)
            gain = (uint8_t)(((uint16_t)gain * cal->follower_low_load_gain) >> 8);
        if (gain == 0) gain = 1;
        filtered = pcm_lag8(requested, pcm->iac.follower_filtered, gain);
    }
    if (!(pcm->iac.kicker_flags & 1u) &&
        (pcm->iac.starting_coolant < cal->hotstart_coolant_minimum ||
         pcm->iac.starting_coolant >= cal->hotstart_coolant_maximum ||
         pcm->scheduler.run_counter > cal->hotstart_runtime_limit)) pcm->iac.kicker_flags |= 1u;
    if ((pcm->iac.learning_flags & 0x80u) || pcm->iac.follower_hold != 0 || (pcm->iac.context & 4u)) {
        if (pcm->iac.context & 4u) pcm->iac.follower_age = 255;
        else { pcm->iac.kicker_flags &= (uint8_t)~2u;pcm->iac.follower_age = 0; }
    } else if (pcm->runtime.deceleration_fuel_cut && !(cal->options & 2u)) pcm->iac.learning_flags |= 0x40u;
    else {
        uint8_t minimum = pcm_lookup16(pcm->iac.coolant_index, cal->follower_minimum);
        uint16_t floor = (uint16_t)((uint16_t)minimum << 8);
        if (!(pcm->iac.kicker_flags & 1u)) floor = four((uint16_t)minimum * cal->follower_start_minimum_gain);
        if (floor > filtered) filtered = floor;
        uint8_t age = pcm->iac.follower_age;
        if (age >= cal->follower_age_limit) pcm->iac.kicker_flags |= 2u;
        else pcm->iac.follower_age = (uint8_t)(age + 1u);
    }
    if (filtered < 40u) filtered = 0;
    pcm->iac.follower_filtered = filtered;
    uint8_t high = (uint8_t)(filtered >> 8);
    if (high < pcm->iac.follower_closed_threshold) { pcm->iac.follower = 0;return PCM_OK; }
    uint16_t next = (uint16_t)(((uint16_t)(high - pcm->iac.follower_closed_threshold) << 8) | (uint8_t)filtered);
    if (pcm->iac.kicker_flags & 2u) next = pcm_gain_word(next, cal->follower_extended_gain[pcm->iac.kicker_flags & 1u]);
    uint8_t gain;
    PcmStatus result = pcm_lookup_scaled(pcm->spark.rpm_high, &cal->follower_rpm, &gain);
    if (result != PCM_OK) return result;
    next = pcm_gain_word(next, gain);
    if (next > 16383u) next = UINT16_MAX;
    else next = four(pcm_gain_word((uint16_t)(4u * next), pcm_lookup16(pcm->iac.coolant_index, cal->follower_coolant)));
    if (!(pcm->iac.kicker_flags & 1u)) next = four(pcm_gain_word(next, cal->follower_start_flow_gain));
    uint16_t old = pcm->iac.follower;
    if (pcm->iac.learning_flags & 0x80u) {
        uint16_t change = next >= old ? (uint16_t)(next - old) : (uint16_t)(old - next);
        if ((change >> 8) < cal->follower_change_limit) return PCM_OK;
    } else if (!pcm->runtime.deceleration_fuel_cut && (pcm->iac.learning_flags & 0x40u)) pcm->iac.learning_flags &= (uint8_t)~0x40u;
    else if (old != 0 && next >= old) return PCM_OK;
    pcm->iac.follower = next;
    return PCM_OK;
}
