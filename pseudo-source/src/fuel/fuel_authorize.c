#include "fuel.h"
#include "hardware.h"
/* AE5C..AE84. The latch has no local clear; zero delta retains its baseline. */
PcmStatus pcm_fuel_authorize(Pcm *pcm)
{
    if (pcm->calibration == NULL) return PCM_BAD_CONFIGURATION;
    if (!(pcm->calibration->mode_d & 0x40u)) { pcm->fuel.authorized = true; return PCM_OK; }
    if (pcm->fuel.authorized) return PCM_OK;
    uint16_t capture;
    PcmStatus result = pcm_read16(pcm, PCM_TIC2, &capture);
    if (result != PCM_OK) return result;
    uint16_t delta = (uint16_t)(capture - pcm->fuel.authorization_capture);
    if (delta == 0) return PCM_OK;
    pcm->fuel.authorization_capture = capture;
    const PcmMixtureCalibration *cal = pcm->calibration->mixture;
    if (cal == NULL) return PCM_BAD_CONFIGURATION;
    if (delta <= cal->authorization_maximum && delta >= cal->authorization_minimum) pcm->fuel.authorized = true;
    return PCM_OK;
}
