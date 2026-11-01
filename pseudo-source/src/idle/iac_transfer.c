#include "iac.h"
/* A154..A287: prepare opposite-gear and opposite-AC work words, with their
 * distinct flag mappings. No proposal directly replaces a learned cell. */
PcmStatus pcm_iac_transfer(Pcm *pcm)
{
    if (!(pcm->iac.context & 8u) || (pcm->iac.context & 0x10u) || pcm->iac.low_battery) return PCM_OK;
    if (pcm->calibration == NULL || pcm->calibration->iac == NULL) return PCM_BAD_CONFIGURATION;
    const PcmIacCalibration *cal = pcm->calibration->iac;
    unsigned ac = (pcm->iac.context & 1u) != 0;
    uint8_t park = (uint8_t)((ac ? pcm->iac.bank[0].ac : pcm->iac.bank[0].no_ac) >> 8);
    uint8_t drive = (uint8_t)((ac ? pcm->iac.bank[1].ac : pcm->iac.bank[1].no_ac) >> 8);
    bool proposal = false;
    if (park >= drive) {
        if ((uint8_t)(park - drive) > cal->park_drive_delta) {
            unsigned current = (pcm->iac.context & 2u) != 0;
            uint8_t high = (uint8_t)((current ? (ac ? pcm->iac.bank[1].ac : pcm->iac.bank[1].no_ac) :
                                                       (ac ? pcm->iac.bank[0].ac : pcm->iac.bank[0].no_ac)) >> 8);
            uint8_t next = current ? (uint8_t)(high + cal->park_drive_delta) : (uint8_t)(high - cal->park_drive_delta);
            pcm->iac.proposed[current ^ 1u][ac] = (uint16_t)((uint16_t)next << 8);proposal = true;
        }
    } else if ((uint8_t)(drive - park) > cal->drive_park_delta) {
        unsigned current = (pcm->iac.context & 2u) != 0;
        uint8_t high = (uint8_t)((current ? (ac ? pcm->iac.bank[1].ac : pcm->iac.bank[1].no_ac) :
                                                   (ac ? pcm->iac.bank[0].ac : pcm->iac.bank[0].no_ac)) >> 8);
        uint8_t next = current ? (uint8_t)(high - cal->drive_park_delta) : (uint8_t)(high + cal->drive_park_delta);
        pcm->iac.proposed[current ^ 1u][ac] = (uint16_t)((uint16_t)next << 8);proposal = true;
    }
    unsigned current = (pcm->iac.context & 2u) != 0;
    ac = (pcm->iac.context & 1u) != 0;
    uint8_t mask = (uint8_t)(1u << (2u * (current ^ 1u) + ac));
    if (proposal) pcm->iac.transfer_flags |= mask;
    else pcm->iac.transfer_flags &= (uint8_t)~mask;
    current = (pcm->iac.context & 2u) != 0;
    uint8_t bound = cal->ac_difference_lower[current];
    uint16_t ac_word = pcm->iac.bank[current].ac, no_ac_word = pcm->iac.bank[current].no_ac;
    uint16_t difference = (uint16_t)(ac_word - no_ac_word);
    bool correction = true;
    if (ac_word > no_ac_word && (difference >> 8) >= bound) {
        bound = cal->ac_difference_upper[current];
        if ((difference >> 8) <= bound) correction = false;
    }
    if (correction) {
        if (!(pcm->iac.context & 1u)) {
            uint16_t sum = (uint16_t)(pcm->iac.bank[current].no_ac >> 8) + bound;
            pcm->iac.proposed[current][1] = sum > 255u ? UINT16_MAX : (uint16_t)(sum << 8);
        } else {
            uint8_t high = (uint8_t)(pcm->iac.bank[current].ac >> 8);
            pcm->iac.proposed[current][0] = high >= bound ? (uint16_t)((uint16_t)(high - bound) << 8) : 0;
        }
    }
    current = (pcm->iac.context & 2u) != 0;
    ac = (pcm->iac.context & 1u) != 0;
    mask = (uint8_t)(1u << (2u * current + (ac ^ 1u)));
    if (correction) pcm->iac.transfer_flags |= mask;
    else pcm->iac.transfer_flags &= (uint8_t)~mask;
    return PCM_OK;
}
