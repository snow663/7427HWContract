#include "fuel.h"

/* BMHM $8EC9..$8EDA. Direction flag $0075.2 is cleared BEFORE the
 * calibration read; if a provider fault occurs, that completed state
 * prefix is intentionally retained. $028E is the high byte of the
 * existing spark RPM-monitor word. */
PcmStatus pcm_fuel_governor_error(Pcm *pcm)
{
    if (pcm==NULL)return PCM_BAD_CONFIGURATION;
    pcm->transmission.governor_flags&=(uint8_t)~0x04u;
    uint8_t target;
    PcmStatus status=pcm_read8(pcm,0x50d8u,&target);
    if(status!=PCM_OK)return status;
    uint8_t actual=(uint8_t)(pcm->spark.rpm_monitor_filtered>>8);
    uint8_t delta=(uint8_t)(target-actual);
    if(target<actual) {
        delta=(uint8_t)(0u-delta);
        pcm->transmission.governor_flags|=0x04u;
    }
    pcm->transmission.governor_speed_error=delta;
    return PCM_OK;
}
