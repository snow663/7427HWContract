#include "iac.h"
/* 920E..9225. Retain the timer when already inactive; set the separate request. */
PcmStatus pcm_iac_kicker_disable(Pcm *pcm)
{
    pcm->iac.kicker_flags &= (uint8_t)~0x18u;
    if (pcm->iac.kicker_flags & 4u) {
        pcm->iac.kicker_timer = 0;
        pcm->iac.kicker_flags &= (uint8_t)~4u;
    }
    if (!(pcm->iac.context & 0x40u)) pcm->iac.context |= 0x40u;
    pcm->iac.kicker_request = true;
    return PCM_OK;
}
