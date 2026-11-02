#include "control.h"
#include "hardware.h"
/* 9167..91A2. This writes only theAA half of the watchdog sequence. */
PcmStatus pcm_input_housekeeping(Pcm *pcm)
{
    PcmStatus result=pcm_write8(pcm,PCM_COPRST,0xaa);
    if (result!=PCM_OK) return result;
    if (pcm->calibration==NULL) return PCM_BAD_CONFIGURATION;
    if (!(pcm->calibration->mode_f&4u)) {
        bool requested=(pcm->iac.input_shadow&1u)!=0;
        pcm->iac.ac_request=requested;pcm->io.ac_mirror=requested;
    }
    pcm->iac.park_neutral=false;
    if (pcm->calibration->mode_f&0x40u) {
        if (!(pcm->iac.input_shadow&0x10u)) pcm->iac.park_neutral=true;
    } else if ((pcm->iac.input_shadow&0x1cu)==0x14u) pcm->iac.park_neutral=true;
    return PCM_OK;
}
