#include "iac.h"
/* A3FA..A406: software homing state; no physical position is inferred. */
PcmStatus pcm_iac_reset_request(Pcm *pcm)
{
    pcm->iac.state_flags |= 1u;
    pcm->iac.context &= (uint8_t)~0x1cu;
    pcm->iac.target = 0;
    pcm->iac.position = 255;
    return PCM_OK;
}
