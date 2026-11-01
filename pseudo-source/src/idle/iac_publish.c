#include "iac.h"
/* A288..A2AF; the direct A29A entry skips both hold decrements. */
PcmStatus pcm_iac_publish(Pcm *pcm, bool age_holds)
{
    if (age_holds) {
        if (pcm->iac.hold[0] != 0) --pcm->iac.hold[0];
        if (pcm->iac.hold[1] != 0) --pcm->iac.hold[1];
    }
    unsigned bank = (pcm->iac.context & 2u) != 0;
    uint8_t snapshot = pcm->iac.bank[bank].no_ac_snapshot;
    if (pcm->iac.context & 1u) snapshot = pcm->iac.bank[bank].ac_snapshot;
    pcm->iac.selected_snapshot = snapshot;
    return PCM_OK;
}
